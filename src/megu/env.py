# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains available environment configs and defaults."""

import os
from pathlib import Path

import environ

from .constants import CACHE_DIR, LOG_DIR, PLUGIN_DIR


@environ.config(prefix="MEGU")
class MeguEnv:
    """Defines available environment configuration values.

    Attributes:
        cache_dir (~pathlib.Path):
            The directory where persistent caches should be stored.
            Read from ``MEGU_CACHE_DIR``.
        log_dir (~pathlib.Path):
            The directory where logs should be stored.
            Read from ``MEGU_LOG_DIR``.
        plugin_dir (~pathlib.Path):
            The directory where plugins will be read from.
            Read from ``MEGU_PLUGIN_DIR``.
    """

    cache_dir: Path = environ.var(default=CACHE_DIR, converter=Path)
    log_dir: Path = environ.var(default=LOG_DIR, converter=Path)
    plugin_dir: Path = environ.var(default=PLUGIN_DIR, converter=Path)


instance: MeguEnv = environ.to_config(MeguEnv, environ=os.environ)
