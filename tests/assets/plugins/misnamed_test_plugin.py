# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""A misnamed test plugin.

This plugin should be completely skipped in plugin discovery.
"""

from megu.plugin import BasePlugin


class MisnamedTestPlugin(BasePlugin):
    ...
