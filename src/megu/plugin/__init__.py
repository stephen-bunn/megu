"""This module contains helpers for the registering and discovery of available plugins."""

from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules
from typing import Generator, Type

from megu.config import APP_NAME, PLUGIN_DIRPATH
from megu.helpers import python_path
from megu.plugin.base import BasePlugin

PLUGIN_PREFIX = f"{APP_NAME}_"
PLUGINS: dict[str, set[BasePlugin]] = {}


def register_plugin(plugin_class: Type[BasePlugin]):
    """Register a plugin for Megu to use.

    This should be called for all exposed plugins as a result of importing a plugin module.
    Do not register a plugin instance, only the class.

    Args:
        plugin_class (Type[BasePlugin]): The plugin class to register for Megu to use.
    """

    plugin_module = plugin_class.__module__.split(".")[0]
    if plugin_module not in PLUGINS:
        PLUGINS[plugin_module] = set()

    PLUGINS[plugin_module].add(plugin_class())


def iter_plugins(
    plugin_dirpath: Path | None = None,
) -> Generator[tuple[str, set[BasePlugin]], None, None]:
    """Iterate over available registered plugins.

    This does not include the :class:`~megu.plugins.generic.GenericPlugin`.

    Args:
        plugin_dirpath (Path | None, optional):
            The directory to search for plugin modules and plugins. Defaults to None.

    Yields:
        tuple[str, set[BasePlugin]]:
            A tuple containing the plugin module name along with the set of
            registered plugin instances.
    """

    if plugin_dirpath is None:
        plugin_dirpath = PLUGIN_DIRPATH

    if not plugin_dirpath.is_dir():
        return

    for dirpath in filter(lambda path: path.is_dir(), plugin_dirpath.iterdir()):
        with python_path(dirpath):
            for _, plugin_name, _ in iter_modules([dirpath.as_posix()]):
                if not plugin_name.startswith(PLUGIN_PREFIX):
                    continue

                try:
                    import_module(plugin_name)
                except Exception:
                    # TODO: probably a good idea to alert that plugin modules cannot be imported
                    # rather than silently passing over them
                    continue

    yield from PLUGINS.items()
