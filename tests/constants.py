# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains test-wide constants."""

from pathlib import Path

ASSETS_DIRPATH = Path(__file__).parent.joinpath("assets").absolute()
PLUGINS_DIRPATH = ASSETS_DIRPATH.joinpath("plugins")

PLUGIN_GOOD = "megu_good_plugin"
