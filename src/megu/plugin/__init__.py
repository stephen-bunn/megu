# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logic for producing and loading plugins for the project."""

from .base import BasePlugin
from .discover import iter_available_plugins

__all__ = ["BasePlugin", "iter_available_plugins"]
