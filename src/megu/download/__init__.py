"""This module contains helpers for the discovery of available downloaders."""

from typing import Generator, Type

from megu.download.base import BaseDownloader
from megu.download.http import HTTPDownloader


def iter_downloaders() -> Generator[Type[BaseDownloader], None, None]:
    """Iterate over available downloader classes.

    Yields:
        Type[BaseDownloader]: An available downloader class.
    """

    yield from [HTTPDownloader]
