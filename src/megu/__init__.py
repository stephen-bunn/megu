# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""The Megu package.

Plugin-centric HTTP media extractor and downloader framework.
"""

from .hasher import HashType
from .models import Checksum, Content, HttpMethod, HttpResource, Manifest, Meta, Url
from .plugin import BasePlugin

__all__ = [
    "BasePlugin",
    "Checksum",
    "Content",
    "HashType",
    "HttpMethod",
    "HttpResource",
    "Manifest",
    "Meta",
    "Url",
]
