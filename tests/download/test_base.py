# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains tests for plugin downloader classes and types."""

import abc

from megu.download import base


def test_BaseDownloader_defined():
    assert issubclass(base.BaseDownloader, abc.ABC)
