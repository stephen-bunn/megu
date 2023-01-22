from typing import Iterator

from megu.download import iter_downloaders
from megu.download.http import HTTPDownloader


def test_iter_downloaders():
    downloader_iterator = iter_downloaders()
    assert isinstance(downloader_iterator, Iterator)
    downloaders = list(downloader_iterator)
    assert HTTPDownloader in downloaders
