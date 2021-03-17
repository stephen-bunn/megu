# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains the functionality to discover the currently available downloaders."""

from typing import Generator, Type

from .base import BaseDownloader
from .http import HttpDownloader


def discover_downloaders() -> Generator[Type[BaseDownloader], None, None]:
    """Discover the available downloaders in the project.

    Yields:
        Type[BaseDownloader]:
            The currently available downloaders.
    """

    yield from [HttpDownloader]
