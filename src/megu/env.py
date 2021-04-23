# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains available environment configs and defaults."""

import os
from pathlib import Path

import environ

from .constants import CACHE_DIRPATH, LOG_DIRPATH, PLUGIN_DIRPATH


@environ.config(prefix="MEGU")
class MeguConfig:
    """Defines available environment configuration values."""

    cache_dir: Path = environ.var(default=CACHE_DIRPATH, converter=Path)
    log_dir: Path = environ.var(default=LOG_DIRPATH, converter=Path)
    plugin_dir: Path = environ.var(default=PLUGIN_DIRPATH, converter=Path)


instance: MeguConfig = environ.to_config(MeguConfig, environ=os.environ)
