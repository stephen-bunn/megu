# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains project wide configuration values."""

from pathlib import Path

import attr

from .constants import APP_NAME, APP_VERSION, STAGING_DIRPATH, TEMP_DIRPATH
from .env import instance as env


@attr.s
class MeguConfig:
    """Project wide configuration values."""

    app_name = APP_NAME
    app_version = APP_VERSION
    temp_dir = TEMP_DIRPATH
    staging_dir = STAGING_DIRPATH

    cache_dir: Path = attr.ib(default=env.cache_dir)
    log_dir: Path = attr.ib(default=env.log_dir)
    plugin_dir: Path = attr.ib(default=env.plugin_dir)


instance = MeguConfig()
