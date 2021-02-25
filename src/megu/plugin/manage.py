# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logic to install plugins into a directory."""


import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ..constants import PLUGIN_DIRPATH
from ..helpers import temporary_directory
from ..log import instance as log
from .discover import discover_plugins

DIST_INFO_PATTERN = r"^(?P<package>.*)-.*\.dist-info$"


def _get_package_name(dirpath: Path) -> Optional[str]:
    """Attempt to extract an installed package's name from it's installed directory.

    .. important::
        This function assumes that the desired package is the ONLY package installed
        in the given directory. Otherwise, this function will return the first
        discovered package ``.dist-info`` and it's name. Please ensure that you are
        using this function in the appropriate context.

    Args:
        dirpath (~pathlib.Path):
            The directory path where the desired package is the only package installed.

    Raises:
        NotADirectoryError:
            If the given ``dirpath`` does not exist.

    Returns:
        Optional[str]:
            The name of the package from ``dist-info`` if available and parseable.
    """

    if not dirpath.is_dir():
        raise NotADirectoryError(f"No such directory {dirpath!s} exists")

    for path in dirpath.iterdir():
        if path.is_file():
            continue

        matches = re.match(DIST_INFO_PATTERN, path.name)
        if not matches:
            continue

        plugin_name = matches.groupdict().get("package", None)
        if not plugin_name:
            continue

        return plugin_name

    return None


def remove_plugin(package: str, plugin_dirpath: Path = PLUGIN_DIRPATH):
    """Remove the given package if it exists in the plugin directory.

    Args:
        package (str):
            The name of the package to remove.
        plugin_dirpath (~pathlib.Path, optional):
            The plugin directory to remove the package from.
            Defaults to ``PLUGIN_DIRPATH``.

    Raises:
        NotADirectoryError:
            If the given package does not exist as a subdirectory within the given
            plugin directory.
    """

    package_dirpath = plugin_dirpath.joinpath(package)
    if not package_dirpath.is_dir():
        raise NotADirectoryError(f"No such directory {package_dirpath!s} exists")

    log.debug(f"Removing the plugin package at {package_dirpath}")
    shutil.rmtree(package_dirpath)


def add_plugin(
    package: str,
    plugin_dirpath: Path = PLUGIN_DIRPATH,
    silence_subprocess: bool = False,
) -> Path:
    """Install a plugin utilizing pip.

    .. important::
        If your package is not installable via pip through any of the distribution
        methods that pip checks (pypi, git, local, etc.), installation of your plugin
        simply will not work.

    Args:
        resource (str):
            The resource that pip should use to discover your plugin.
        plugin_dirpath (~pathlib.Path, optional):
            The directory the plugin should be installed to.
            Defaults to ``PLUGIN_DIRPATH``.
        silence_subprocess (bool):
            If set to ``True``, will redirect output of subprocess calls to /dev/null.
            Defaults to ``False``.

    Returns:
        ~pathlib.Path:
            The directory the plugin was installed to.
    """

    out_handle = subprocess.DEVNULL if silence_subprocess else sys.stdout
    err_handle = subprocess.DEVNULL if silence_subprocess else sys.stderr

    with temporary_directory("plugin-install-") as temp_dirpath:
        call_args = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            package,
            "--target",
            temp_dirpath.as_posix(),
            "--progress-bar",
            "off",
            "--no-color",
        ]

        try:
            log.info(f"Installing plugin from {package!s} via pip using {call_args!r}")
            subprocess.check_call(
                call_args,
                stdout=out_handle,  # type: ignore
                stderr=err_handle,  # type: ignore
            )
        except subprocess.CalledProcessError:
            log.exception(
                f"Failed to install plugin from {package!s} via pip using {call_args!r}"
            )
            raise

        package_name = _get_package_name(temp_dirpath)
        if package_name is None:
            raise ValueError(
                f"Failed to extract package name from package at {temp_dirpath}"
            )

        installed = list(discover_plugins(temp_dirpath))
        if len(installed) <= 0:
            raise ValueError(f"Package at {temp_dirpath} exposes no plugins")

        package_dirpath = plugin_dirpath.joinpath(package_name)
        if package_dirpath.is_dir():
            raise IsADirectoryError(
                f"Plugin directory at {package_dirpath!s} already exists"
            )

        log.debug(
            f"Moving installed package {package_name} at {temp_dirpath} to "
            f"{package_dirpath}"
        )
        shutil.copytree(temp_dirpath, package_dirpath)

        log.success(f"Installed plugin {package_name} to {package_dirpath}")
        return package_dirpath
