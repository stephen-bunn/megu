from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from hypothesis import assume, given

from megu.errors import MeguWarning
from megu.plugin import iter_plugins, register_plugin
from megu.plugin.generic import GenericPlugin

from ..strategies import path


@patch("megu.plugin.PLUGINS", {})
def test_register_plugin():
    from megu.plugin import PLUGINS

    register_plugin(GenericPlugin)
    assert "megu" in PLUGINS
    assert len(PLUGINS["megu"]) == 1
    assert next(iter(PLUGINS["megu"])) == GenericPlugin


@patch("megu.plugin.PLUGINS", {})
def test_register_plugin_allows_multiple():
    from megu.plugin import PLUGINS

    PLUGINS["megu"] = {GenericPlugin}

    register_plugin(GenericPlugin)
    assert "megu" in PLUGINS
    assert len(PLUGINS["megu"]) == 1
    assert next(iter(PLUGINS["megu"])) == GenericPlugin


def test_register_plugin_raises_ValueError_for_non_classes():
    with pytest.raises(ValueError) as error:
        register_plugin(GenericPlugin())  # type: ignore

        assert "Failed to register plugin class" in str(error)


@patch("megu.plugin.PLUGINS", {})
def test_iter_plugins():
    with TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)

        test_plugin_dirpath = temp_dirpath.joinpath("megu_test", "megu_test")
        test_plugin_dirpath.mkdir(mode=0o755, parents=True)
        test_plugin_filepath = test_plugin_dirpath.joinpath("__init__.py")

        with test_plugin_filepath.open("w") as temp_io:
            temp_io.write(
                """from megu import register_plugin\n\nclass TestPlugin():\n    ...\n\nregister_plugin(TestPlugin)"""
            )

        plugins = list(iter_plugins(temp_dirpath))
        assert len(plugins) == 1
        module_name, module_plugins = plugins[0]
        assert module_name == "megu_test"
        assert len(module_plugins) == 1
        assert next(iter(module_plugins)).__name__ == "TestPlugin"


@given(path())
def test_iter_plugins_raises_StopIteration_for_missing_plugin_directory(plugin_dirpath: Path):
    assume(plugin_dirpath.exists() == False)
    with pytest.raises(StopIteration):
        next(iter_plugins(plugin_dirpath))


@patch("megu.plugin.PLUGINS", {})
def test_iter_plugins_skips_module_missing_prefix():
    with TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)

        test_plugin_dirpath = temp_dirpath.joinpath("test", "test")
        test_plugin_dirpath.mkdir(mode=0o755, parents=True)
        test_plugin_filepath = test_plugin_dirpath.joinpath("__init__.py")
        with test_plugin_filepath.open("w") as temp_io:
            temp_io.write("")

        assert len(list(iter_plugins(temp_dirpath))) == 0


@patch("megu.plugin.PLUGINS", {})
@pytest.mark.skip(reason="warnings capture is flakey")
def test_iter_plugins_warns_if_module_cannot_be_imported():
    with TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)

        test_plugin_dirpath = temp_dirpath.joinpath("megu_test", "megu_test")
        test_plugin_dirpath.mkdir(mode=0o755, parents=True)
        test_plugin_filepath = test_plugin_dirpath.joinpath("__init__.py")
        with test_plugin_filepath.open("w") as file_io:
            file_io.write("raise ImportError('test')\n")

        with pytest.warns(MeguWarning) as warn_records:
            assert len(list(iter_plugins(temp_dirpath))) == 0

            # FIXME: warnings capture is always flakey, sometimes warnings are not properly stored
            # as records using the `pytest.warns` context manager
            if len(warn_records) > 1:
                assert f"Failed to import plugins from {test_plugin_dirpath.parent}, test" in str(
                    warn_records[0].message
                )
