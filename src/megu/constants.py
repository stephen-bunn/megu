# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains project-wide constants."""

import tempfile
from pathlib import Path

import appdirs

APP_NAME = "megu"
APP_VERSION = "0.1.0"

app_dirs = appdirs.AppDirs(appname=APP_NAME)

CONFIG_DIRPATH = Path(app_dirs.user_config_dir).absolute()
CACHE_DIRPATH = Path(app_dirs.user_cache_dir).absolute()
LOG_DIRPATH = Path(app_dirs.user_log_dir).absolute()
PLUGIN_DIRPATH = CONFIG_DIRPATH.joinpath("plugins")
TEMP_DIRPATH = Path(tempfile.gettempdir()).joinpath(APP_NAME)
STAGING_DIRPATH = TEMP_DIRPATH.joinpath(".staging")
