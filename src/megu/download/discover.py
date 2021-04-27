# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains the functionality to discover the currently available downloaders."""

from typing import Generator, Type

from .base import BaseDownloader
from .http import HttpDownloader


def discover_downloaders() -> Generator[Type[BaseDownloader], None, None]:
    """Discover the available downloaders in the project.

    Yields:
        Type[:class:`~megu.download.base.BaseDownloader`]:
            The currently available downloaders.
    """

    yield from [HttpDownloader]
