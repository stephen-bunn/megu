# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""A proper testing plugin."""

from megu.plugin import BasePlugin


class MiscellaneousClass(object):
    ...


class MeguTestPlugin(BasePlugin):
    name = "Test Plugin"
    domains = {"google.com"}

    def can_handle(self, url):
        return True

    def extract_content(self, url):
        ...


class MeguSecondTestPlugin(BasePlugin):
    name = "Second Test Plugin"
    domains = {"google.com"}

    def can_handle(self, url):
        return True

    def extract_content(self, url):
        ...
