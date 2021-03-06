# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains utilities for the framework to use.

These helper/utility functions should **not** be exposed to plugins.
"""

from megu.constants import (
    CACHE_DIRPATH,
    CONFIG_DIRPATH,
    LOG_DIRPATH,
    PLUGIN_DIRPATH,
    TEMP_DIRPATH,
)
from megu.log import instance as log


def create_required_directories():
    """Handle setting up the required directories on the local machine."""

    for required_dirpath in (
        CACHE_DIRPATH,
        CONFIG_DIRPATH,
        LOG_DIRPATH,
        PLUGIN_DIRPATH,
        TEMP_DIRPATH,
    ):
        if not required_dirpath.is_dir():
            log.info(f"Creating required directory at {required_dirpath}")
            required_dirpath.mkdir(mode=0o777)
