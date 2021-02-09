# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains helper methods that plugins can use to simplify usage."""

from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import IO, Generator, Tuple

from bs4 import BeautifulSoup
from requests import Session

from .constants import TEMP_DIRPATH


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
            Defaults to ``TEMP_DIRPATH``.

    Yields:
        Tuple[~pathlib.Path, IO]:
            A tuple containing the temporary file's path and the file handle.
    """

    with NamedTemporaryFile(
        prefix=f"{prefix!s}-",
        mode=mode,
        dir=dirpath,
    ) as temp_handle:
        yield Path(temp_handle.name), temp_handle


def get_soup(markup: str) -> BeautifulSoup:
    """Get a BeautifulSoup instance for some HTML markup.

    Args:
        markup (str):
            The HTML markup to use when building a BeautifulSoup instance.

    Returns:
        :class:`~bs4.BeautifulSoup`:
            The parsed soup for the given HTML markup.
    """

    return BeautifulSoup(markup=markup, features="lxml")
