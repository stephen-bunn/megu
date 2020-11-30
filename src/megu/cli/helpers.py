# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains generic helpers that the CLI needs to isolate."""

from ..constants import CONFIG_DIRPATH, LOG_DIRPATH, PLUGIN_DIRPATH
from ..log import instance as log


def setup_app():
    """Handle setting up the application environment on the local machine."""

    for required_dirpath in (
        CONFIG_DIRPATH,
        PLUGIN_DIRPATH,
        LOG_DIRPATH,
    ):
        if not required_dirpath.is_dir():
            log.info(f"Creating required directory at {required_dirpath!s}")
            required_dirpath.mkdir(mode=0o777)
