# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains helper methods that plugins can use to simplify usage."""

import re
import sys
from contextlib import contextmanager
from os import PathLike
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import IO, Generator, List, Tuple

from bs4 import BeautifulSoup
from diskcache import Cache
from requests import Session

from .constants import CACHE_DIRPATH, TEMP_DIRPATH
from .log import instance as log

DISK_CACHE_PATTERN = re.compile(r"^[a-z]+[a-z0-9_-]{3,31}[a-z0-9]$")


class noop_class:
    """Noop class that allows for everything but does nothing."""

    def __init__(*args, **kwargs):
        """Noop class initialization (does nothing)."""

        pass

    def __call__(self, *args, **kwargs):
        """Noop class call (returns itself)."""

        return self

    def __getattr__(self, *args, **kwargs):
        """Noop getter (returns itself)."""

        return self


def noop(*args, **kwargs) -> None:
    """Noop function that does absolutely nothing."""

    return None


@contextmanager
def http_session() -> Generator[Session, None, None]:
    """Context manager for creating a requests HTTP session to make basic requests.

    Yields:
        :class:`~requests.Session`:
            A new clean session that plugins can use for requests.
    """

    with Session() as session:
        yield session


@contextmanager
def disk_cache(cache_name: str) -> Generator[Cache, None, None]:
    """Context manager for creating or accessing a local disk cache.

    We recommend that you avoid using a diskcache if at all possible.
    The feature to define and use a disk-persisted cache was introduced for the purpose
    of caching fetched API tokens between runs (such as OAuth Bearer tokens).
    You should **not** be caching content, you should be downloading content.

    .. important::
        For some relatively naive precautions, we don't allow for path separators or
        spaces in the cache name.
        For this purpose, we are enforcing that the name of the cache must match the
        following pattern: ``^[a-z]+[a-z0-9_-]{3,31}[a-z0-9]$``.

        For this reason, we recommend that you use your plugin's package name as the
        name for your plugin's disk-persisted cache.

    .. warning::
        Please be reasonable about what you are caching.
        No one wants people taking advantage of their disk-space.

    Args:
        cache_name (str):
            The name of the cache to create or access.

    Raises:
        ValueError:
            If the given ``cache_name`` does not match the approved naming pattern.

    Yields:
        :class:`~diskcache.Cache`:
            The diskcache Cache instance.
    """

    if not DISK_CACHE_PATTERN.match(cache_name):
        raise ValueError(
            f"Disk cache name {cache_name!r} violates the required naming pattern "
            f"{DISK_CACHE_PATTERN.pattern!r}"
        )

    diskcache_dirpath = CACHE_DIRPATH.joinpath(cache_name)
    if not diskcache_dirpath.is_dir():
        log.debug(f"Creating a new diskcache at {diskcache_dirpath}")
        diskcache_dirpath.mkdir(mode=0o777, parents=True)

    with Cache(diskcache_dirpath.as_posix()) as cache:
        yield cache


@contextmanager
def temporary_file(
    prefix: str,
    mode: str,
    dirpath: Path = TEMP_DIRPATH,
) -> Generator[Tuple[Path, IO], None, None]:
    """Context manager for opening a temporary file at the appropriate location.

    Args:
        prefix (str):
            The prefix of the temporary file.
        mode (str):
            The mode the file should be opened with.
        dirpath (~pathlib.Path, optional):
            The directory path the temporary file should be opened in.
            Defaults to :attr:`~megu.constants.TEMP_DIRPATH`.

    Raises:
        NotADirectoryError:
            When the provided ``dirpath`` does not exist.s

    Yields:
        Tuple[:class:`~pathlib.Path`, :class:`~typing.IO`]:
            A tuple containing the temporary file's path and the file handle.
    """

    if not dirpath.is_dir():
        raise NotADirectoryError(f"No such directory {dirpath} exists")

    with NamedTemporaryFile(
        prefix=f"{prefix!s}-",
        mode=mode,
        dir=dirpath,
    ) as temp_handle:
        log.debug(f"Creating temporary file at {temp_handle.name}")
        yield Path(temp_handle.name), temp_handle


@contextmanager
def temporary_directory(
    prefix: str, dirpath: Path = TEMP_DIRPATH
) -> Generator[Path, None, None]:
    """Context manager for creating a temporary directory at the appropriate location.

    Args:
        prefix (str):
            The prefix of the temporary directory.
        dirpath (~pathlib.Path, optional):
            The directory path the temporary directory should be created in.
            Defaults to :attr:`~megu.constants.TEMP_DIRPATH`.

    Raises:
        NotADirectoryError:
            When the provided ``dirpath`` does not exist.

    Yields:
        :class:`~pathlib.Path`:
            The temporary directory's path.
    """

    if not dirpath.is_dir():
        raise NotADirectoryError(f"No such directory {dirpath} exists")

    with TemporaryDirectory(prefix=prefix, dir=dirpath) as temp_dir:
        log.debug(f"Creating temporary directory at {temp_dir}")
        yield Path(temp_dir)


@contextmanager
def python_path(*paths: PathLike) -> Generator[List[str], None, None]:
    """Context manager for temporarily added directories to the Python search path.

    Args:
        *paths (Tuple[~os.PathLike]):
            The paths of directories that you want to add to the Python path.

    Yields:
        List[str]:
            The temporarily mutated ``sys.path``.
    """

    original_paths = sys.path.copy()
    try:
        if len(paths) <= 0:
            yield sys.path
        else:
            for directory_name in paths:
                directory_path = Path(directory_name).expanduser().resolve()
                if not directory_path.is_dir() or directory_path.as_posix() in sys.path:
                    log.warning(
                        f"Skipping inserting the directory {directory_path!s} into the "
                        "Python path, is not a directory or already present"
                    )
                    continue

                log.debug(
                    f"Inserting directory {directory_path!s} into the Python path"
                )
                sys.path.insert(0, directory_path.as_posix())

            yield sys.path
    finally:
        log.debug("Restoring original Python path")
        sys.path = original_paths


def get_soup(markup: str) -> BeautifulSoup:
    """Get a BeautifulSoup instance for some HTML markup.

    Args:
        markup (str):
            The HTML markup to use when building a BeautifulSoup instance.

    Returns:
        ~bs4.BeautifulSoup:
            The parsed soup for the given HTML markup.
    """

    return BeautifulSoup(markup=markup, features="lxml")
