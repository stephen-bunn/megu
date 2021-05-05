# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains project-wide constants.

Attributes:
    APP_NAME (str):
        The name of the application.
        Should always be ``megu``.
    APP_VERSION (str):
        The current version of the megu application.
    CONFIG_DIR (~pathlib.Path):
        The directory path where the application configuration lives.
    PLUGIN_DIR (~pathlib.Path):
        The directory path where plugins are installed to.
    CACHE_DIR (~pathlib.Path):
        The directory path where the application cache lives.
    LOG_DIR (~pathlib.Path):
        The directory path where the application logs live.
    TEMP_DIR (~pathlib.Path):
        The directory path where the application temporary files live.
    STAGING_DIR (~pathlib.Path):
        The directory path where the application downloads content fragments to.
    DOWNLOAD_DIR (~pathlib.Path):
        The directory path where downloads are stored to by default.
"""

import tempfile
from pathlib import Path

import appdirs

APP_NAME = "megu"
APP_VERSION = "0.1.0"

app_dirs = appdirs.AppDirs(appname=APP_NAME)

CONFIG_DIR = Path(app_dirs.user_config_dir).absolute()
CACHE_DIR = Path(app_dirs.user_cache_dir).absolute()
LOG_DIR = Path(app_dirs.user_log_dir).absolute()
PLUGIN_DIR = CONFIG_DIR.joinpath("plugins")
TEMP_DIR = Path(tempfile.gettempdir()).joinpath(APP_NAME)
STAGING_DIR = TEMP_DIR.joinpath(".staging")
DOWNLOAD_DIR = Path.home().joinpath("Downloads").absolute()
