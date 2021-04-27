# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains tests for plugin base classes and types."""

import abc

from megu.plugin import base


def test_BasePlugin_defined():
    assert issubclass(base.BasePlugin, abc.ABC)
