# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains available environment configs and defaults."""

import os
from pathlib import Path

import environ

from .constants import CACHE_DIR, LOG_DIR, PLUGIN_DIR


@environ.config(prefix="MEGU")
class MeguEnv:
    """Defines available environment configuration values."""

    cache_dir: Path = environ.var(default=CACHE_DIR, converter=Path)
    log_dir: Path = environ.var(default=LOG_DIR, converter=Path)
    plugin_dir: Path = environ.var(default=PLUGIN_DIR, converter=Path)


instance: MeguEnv = environ.to_config(MeguEnv, environ=os.environ)
