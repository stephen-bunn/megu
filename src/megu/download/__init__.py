# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains the namespace for content downloaders."""

from typing import Type

from ..types import Content
from .base import BaseDownloader
from .http import HttpDownloader

AVAILABLE_DOWNLOADERS = (HttpDownloader,)


def get_downloader(content: Content) -> Type[BaseDownloader]:
    """Get the appropriate downloader for some extracted content.

    Args:
        content (~types.Content):
            The content we need the attempted downloader.

    Returns:
        Type[~.base.BaseDownloader]:
            The appropriate downloader for the given content.
    """

    for downloader in AVAILABLE_DOWNLOADERS:
        if not downloader.can_handle(content):
            continue

        return downloader

    # we assume that we can attempt to fetch the content via HTTP if no downloaders
    # report that they can handle the given content.
    return HttpDownloader


__all__ = ["get_downloader", "HttpDownloader"]
