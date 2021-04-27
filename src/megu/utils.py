# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains utilities for the framework to use.

These helper/utility functions should **not** be exposed to plugins.
"""

from pathlib import Path

from .config import instance as config
from .log import instance as log

REQUIRED_DIRECTORIES = (
    config.cache_dir,
    config.log_dir,
    config.plugin_dir,
    config.temp_dir,
)


def create_required_directories():
    """Handle setting up the required directories on the local machine."""

    for required_dirpath in REQUIRED_DIRECTORIES:
        if not required_dirpath.is_dir():
            log.info(f"Creating required directory at {required_dirpath}")
            required_dirpath.mkdir(mode=0o777, parents=True)


def allocate_storage(to_path: Path, size: int) -> Path:
    """Allocate a specific number of bytes to a non-existing filepath.

    Args:
        to_path (~pathlib.Path):
            The filepath to allocate a specific number of bytes to.
        size (int):
            The number of bytes to allocate.

    Raises:
        FileExistsError:
            If the given filepath already exists

    Returns:
        ~pathlib.Path: The given filepath
    """

    if size <= 0:
        raise ValueError(f"Expected byte size > 0 to allocate, received {size!s}")

    if to_path.exists():
        raise FileExistsError(f"File at {to_path!s} already exists")

    if not to_path.parent.is_dir():
        log.debug(f"Creating directory {to_path.parent!s} to allocate {to_path!s}")
        to_path.parent.mkdir(mode=0o777, parents=True)

    log.info(f"Allocating {size!s} bytes at {to_path!s}")
    with to_path.open("wb") as file_handle:
        file_handle.seek(size - 1)
        file_handle.write(b"\x00")

    return to_path
