# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for downloader discovery."""

from typing import Generator

from megu.download.base import BaseDownloader
from megu.download.discover import discover_downloaders


def test_discover_downloaders():
    downloader_generator = discover_downloaders()
    assert isinstance(downloader_generator, Generator)

    for downloader in downloader_generator:
        assert issubclass(downloader, BaseDownloader)
