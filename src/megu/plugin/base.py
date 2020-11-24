# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains the abstractions necessary for the plugin discovery to work."""

import abc


class BasePlugin(abc.ABC):
    """The base plugin that all plugins should inherit from."""

    ...
