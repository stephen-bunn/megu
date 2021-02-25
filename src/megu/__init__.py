# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""The Megu package.

Plugin-centric HTTP media extractor and downloader framework.
"""

from .hasher import HashType
from .log import instance as log
from .models import Checksum, Content, HttpMethod, HttpResource, Manifest, Meta, Url
from .plugin import BasePlugin

__all__ = [
    "BasePlugin",
    "Checksum",
    "Content",
    "HashType",
    "HttpMethod",
    "HttpResource",
    "log",
    "Manifest",
    "Meta",
    "Url",
]
