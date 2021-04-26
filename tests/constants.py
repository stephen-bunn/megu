# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains test-wide constants."""

from pathlib import Path

ASSETS_DIR = Path(__file__).parent.joinpath("assets").absolute()
PLUGINS_DIR = ASSETS_DIR.joinpath("plugins")

PLUGIN_GOOD = "megu_good_plugin"
