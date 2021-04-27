# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains the namespace for content downloaders."""

from .base import BaseDownloader
from .discover import discover_downloaders
from .http import HttpDownloader

__all__ = ["discover_downloaders", "BaseDownloader", "HttpDownloader"]
