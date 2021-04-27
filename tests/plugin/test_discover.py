# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains tests for plugin discovery."""

from functools import partial
from pathlib import Path
from types import ModuleType
from typing import Generator

import pytest
from hypothesis import given

from megu.exceptions import PluginFailure
from megu.helpers import python_path
from megu.plugin.base import BasePlugin
from megu.plugin.discover import (
    discover_plugins,
    iter_available_plugins,
    load_plugin,
    load_plugin_module,
)

from ..assets.plugins.megu_bad_plugin import MeguBadPlugin
from ..assets.plugins.megu_good_plugin import MeguGoodPlugin, MeguGoodPlugin2
from ..strategies import pythonic_name

ASSET_PLUGIN_DIR = Path(__file__).parent.parent.joinpath("assets", "plugins")
_plugin_context = partial(python_path, ASSET_PLUGIN_DIR)


def test_load_plugin():
    with _plugin_context():
        plugin = load_plugin("megu_good_plugin", MeguGoodPlugin)
        assert isinstance(plugin, BasePlugin)
        assert isinstance(plugin, MeguGoodPlugin)


def test_load_plugin_raises_PluginFailure():
    with pytest.raises(PluginFailure):
        load_plugin("test", MeguBadPlugin)


def test_load_plugin_module():
    with _plugin_context():
        module = load_plugin_module("megu_good_plugin")
        assert isinstance(module, ModuleType)


@given(pythonic_name())
def test_load_plugin_module_raises_PluginFailure(plugin_name: str):
    with pytest.raises(PluginFailure):
        load_plugin_module(plugin_name)


def test_discover_plugins():
    discovered_generator = discover_plugins(ASSET_PLUGIN_DIR)
    assert isinstance(discovered_generator, Generator)
    discovered = list(discovered_generator)
    assert len(discovered) == 1

    # only plugin that should be discovered is the "good" one
    plugin_name, plugins = discovered[0]
    assert plugin_name == "megu_good_plugin"
    assert len(plugins) == 2


def test_iter_available_plugins():
    iterator = iter_available_plugins(ASSET_PLUGIN_DIR.parent)
    assert isinstance(iterator, Generator)
    discovered = list(iterator)
    assert len(discovered) == 1

    # only plugin that should be discovered is the "good" one
    plugin_name, plugins = discovered[0]
    assert plugin_name == "megu_good_plugin"
    assert len(plugins) == 2
