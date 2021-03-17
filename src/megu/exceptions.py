# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains definitions for custom project exceptions."""


class MeguException(Exception):
    """Provides a namespace for the project specific exceptions."""

    def __init__(self, message: str):
        """Initialize the global project exception.

        Args:
            message (str):
                The exception message.
        """

        super().__init__(message)
        self.message = message


class PluginFailure(MeguException):
    """Describes when a plugin fails to load for some reason."""

    ...
