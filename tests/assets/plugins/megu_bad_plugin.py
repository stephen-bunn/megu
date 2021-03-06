# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""A bad plugin.

This plugin should be completely skipped since it can't be initialized.
"""

from megu.plugin import BasePlugin


class MeguBadPlugin(BasePlugin):
    def __init__(self):
        raise RuntimeError("Forced failure on plugin initialization")
