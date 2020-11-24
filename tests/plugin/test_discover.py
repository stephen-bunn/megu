# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for plugin discovery."""

from megu.plugin import discover

from ..constants import PLUGIN_GOOD, PLUGINS_DIRPATH

# FIXME: these tests are currently not fleshed out to cover the whole module
# Right now, this tests operates with just inputs and outputs rather than testing
# actual functionality


def test_discover_plugins():
    plugins = dict(discover.discover_plugins(PLUGINS_DIRPATH))

    assert PLUGIN_GOOD in plugins
    assert len(plugins[PLUGIN_GOOD]) == 2
