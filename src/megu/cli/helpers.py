# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains generic helpers that the CLI needs to isolate."""

from functools import lru_cache
from typing import Dict, List

from ..constants import CONFIG_DIRPATH, LOG_DIRPATH, PLUGIN_DIRPATH
from ..log import instance as log
from ..plugin.base import BasePlugin
from ..plugin.discover import discover_plugins


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


@lru_cache
def get_plugins() -> Dict[str, List[BasePlugin]]:
    """Get the default dictionary of plugins available.

    Returns:
        Dict[str, List[:class:`~.plugin.base.BasePlugin`]]:
            The dictionary of available plugins.
    """

    return dict(discover_plugins(PLUGIN_DIRPATH))
