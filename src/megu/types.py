"""This module contains arbitrary types that don't fit into any existing namespaces."""

from typing import Any, Callable

"""Describes the callable signature for an update hook.

This is a callable that takes an incremented value to a total.
The total amount should be passed in as the second value, but it is optional.
"""
UpdateHook = Callable[[int, int | None], Any]
