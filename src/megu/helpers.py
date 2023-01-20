"""This module provides several helpers that plugins may make use of.

Attributes:
    DISK_CACHE_PATTERN (re.Pattern):
        The cache name pattern that diskcache caches must use.
"""

import re
import sys
from contextlib import contextmanager
from os import PathLike
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import IO, Generator

from diskcache import Cache
from httpx import Client

from megu.config import CACHE_DIRPATH, TEMPORARY_DIRPATH

DISK_CACHE_PATTERN = re.compile(r"^[a-z]+[a-z0-9_-]{3,31}[a-z0-9]$")


@contextmanager
def http_session() -> Generator[Client, None, None]:
    """Context manager for getting an httpx client.

    >>> with http_session() as session:
    >>>     response = client.get("https://www.google.com/")
    >>>     print(response.status_code)
    200

    Once the context is exited, the provided client is closed.

    Yields:
        Client: A context-specific httpx client.
    """

    client = Client()
    try:
        yield client
    finally:
        client.close()


def allocate_storage(to_path: Path, size: int) -> Path:
    """Allocate some filepath with the given byte size.

    Args:
        to_path (Path): The filepath to allocate.
        size (int): The size in bytes to allocate to the given filepath.

    Raises:
        ValueError: If the given size is not greater than 0.
        FileExistsError: If the given filepath already exists.

    Returns:
        Path: The allocated filepath.
    """

    if size <= 0:
        raise ValueError(f"Expected byte size > 0 to allocate, received {size}")

    if to_path.exists():
        raise FileExistsError(f"File at {to_path} already exists")

    if not to_path.parent.is_dir():
        to_path.parent.mkdir(mode=0o777, parents=True)

    with to_path.open("wb") as file_handle:
        file_handle.seek(size - 1)
        file_handle.write(b"\x00")

    return to_path


@contextmanager
def temporary_file(
    prefix: str, mode: str, dirpath: Path | None = None
) -> Generator[tuple[Path, IO], None, None]:
    """Context manager to generate a temporary file.

    Args:
        prefix (str): The prefix to use for the temporary file.
        mode (str): The mode to open the temporary file as.
        dirpath (Path | None, optional):
            The directory to use as the parent of the generated temporary file. Defaults to None.

    Raises:
        NotADirectoryError: If the provided dirpath is not an existing directory.

    Yields:
        tuple[Path, IO]:
            A tuple containing the filepath of the temporary file and the file handle
            for the temporary file
    """
    if dirpath is None:
        dirpath = TEMPORARY_DIRPATH

    if not dirpath.is_dir():
        raise NotADirectoryError(f"No directory at {dirpath} exists")

    with NamedTemporaryFile(prefix=prefix, mode=mode, dir=dirpath) as temp_io:
        yield Path(temp_io.name), temp_io


@contextmanager
def temporary_directory(prefix: str, dirpath: Path | None = None) -> Generator[Path, None, None]:
    """Context manager to generate a temporary directory.

    Args:
        prefix (str): The prefix of the temporary directory to produce.
        dirpath (Path | None, optional):
            The directory to use as the parent of the generated temporary directory.
            Defaults to None.

    Raises:
        NotADirectoryError: If the provided dirpath is not an existing directory.

    Yields:
        Path: The dirpath of the generated temporary directory.
    """

    if dirpath is None:
        dirpath = TEMPORARY_DIRPATH

    if not dirpath.is_dir():
        raise NotADirectoryError(f"No directory at {dirpath} exists")

    with TemporaryDirectory(prefix=prefix, dir=dirpath) as temp_dir:
        yield Path(temp_dir)


@contextmanager
def python_path(*paths: PathLike) -> Generator[list[str], None, None]:
    """Context manager to temporarily insert paths into the `PYTHON_PATH`.

    Yields:
        list[str]: The list containing temporary Python paths within the context.
    """

    original_paths = sys.path.copy()
    try:
        if len(paths) <= 0:
            yield sys.path
        else:
            for directory_name in paths:
                directory_path = Path(directory_name).expanduser().resolve()
                if not directory_path.is_dir():
                    continue

                if directory_path.as_posix() in sys.path:
                    continue

                sys.path.insert(0, directory_path.as_posix())

            yield sys.path

    finally:
        sys.path = original_paths


@contextmanager
def disk_cache(cache_name: str) -> Generator[Cache, None, None]:
    """Get a specific diskcache instance for a given cache name.

    Args:
        cache_name (str): The name of the cache to get.

    Raises:
        ValueError: If the provided cache name does not match the required pattern.

    Yields:
        Cache: The diskcache instance for the given cache name.
    """

    if not DISK_CACHE_PATTERN.match(cache_name):
        raise ValueError(
            f"Disk cache name {cache_name!r} violates the required naming pattern "
            f"{DISK_CACHE_PATTERN.pattern!r}"
        )

    diskcache_dirpath = CACHE_DIRPATH.joinpath(cache_name)
    if not diskcache_dirpath.is_dir():
        diskcache_dirpath.mkdir(mode=0o755, parents=True, exist_ok=True)

    with Cache(diskcache_dirpath.as_posix()) as cache:
        yield cache
