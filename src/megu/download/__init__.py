from typing import Generator, Type

from megu.download.base import BaseDownloader
from megu.download.http import HttpDownloader


def iter_downloaders() -> Generator[Type[BaseDownloader], None, None]:
    yield from [HttpDownloader]
