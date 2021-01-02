# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains helper methods that plugins can use to simplify usage."""

from requests import Session


def get_session() -> Session:
    """Get a requests HTTP session for making basic requests.

    Returns:
        :class:`~requests.Session`:
            A new clean session that plugins can use for requests.
    """

    return Session()
