# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logic to install plugins into a directory."""

# FIXME: ATM this is a very naive installation process, there is no verification and
# no real interesting return values. This is currently in place to help development.

import subprocess
import sys
from pathlib import Path

from ..constants import PLUGIN_DIRPATH
from ..log import instance as log


def install_plugin(resource: str, to_dir: Path = PLUGIN_DIRPATH):
    """Install a plugin utilizing pip.

    .. important::
        If your package is not installable via pip through any of the distribution
        methods that pip checks (pypi, git, local, etc.), installation of your plugin
        simply will not work.

    Args:
        resource (str):
            The resource that pip should use to discover your plugin.
        to_dir (~pathlib.Path, optional):
            The directory the plugin should be installed to.
            Defaults to PLUGIN_DIRPATH.
    """

    log.info(f"Installing plugin from {resource!s} via pip")
    call_args = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        resource,
        "--target",
        to_dir.as_posix(),
    ]

    log.debug(f"Calling subprocess with args {call_args!r}")
    subprocess.check_call(
        call_args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
