# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""A bad plugin.

This plugin should be completely skipped since it can't be initialized.
"""

from megu.plugin import BasePlugin


class MeguTestPlugin(BasePlugin):
    def __init__(self):
        raise RuntimeError("Forced failure on plugin initialization")
