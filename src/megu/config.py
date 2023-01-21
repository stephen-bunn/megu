"""This module contains configuration globals used throughout the library."""

from pathlib import Path
from tempfile import gettempdir

from appdirs import AppDirs

APP_NAME = "megu"
APP_DIRS = AppDirs(APP_NAME)

CONFIG_DIRPATH = Path(APP_DIRS.user_config_dir).absolute()
CACHE_DIRPATH = Path(APP_DIRS.user_cache_dir).absolute()
PLUGIN_DIRPATH = CONFIG_DIRPATH.joinpath("plugins")
PLUGIN_PREFIX = f"{APP_NAME}_"
DOWNLOAD_DIRPATH = Path.home().joinpath("Downloads").absolute()
TEMPORARY_DIRPATH = Path(gettempdir()).joinpath(APP_NAME)
STAGING_DIRPATH = TEMPORARY_DIRPATH.joinpath(".staging")
