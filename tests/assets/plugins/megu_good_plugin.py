# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""A proper testing plugin."""

from megu.plugin import BasePlugin


class MiscellaneousClass(object):
    ...


class MeguTestPlugin(BasePlugin):
    ...


class MeguSecondTestPlugin(BasePlugin):
    ...
