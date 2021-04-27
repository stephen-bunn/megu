# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""A misnamed test plugin.

This plugin should be completely skipped in plugin discovery.
"""

from megu.plugin import BasePlugin


class MisnamedTestPlugin(BasePlugin):
    ...
