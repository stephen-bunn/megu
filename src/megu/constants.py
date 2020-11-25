# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains project-wide constants."""

from pathlib import Path

import typer

APP_NAME = "megu"
APP_VERSION = "0.1.0"

CONFIG_DIRPATH = Path(typer.get_app_dir(app_name=APP_NAME)).absolute()
LOG_DIRPATH = CONFIG_DIRPATH.joinpath("logs")
PLUGIN_DIRPATH = CONFIG_DIRPATH.joinpath("plugins")
