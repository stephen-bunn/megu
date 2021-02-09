# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains helper methods that plugins can use to simplify usage."""

from contextlib import contextmanager
from typing import Generator

from bs4 import BeautifulSoup
from requests import Session


@contextmanager
def use_session() -> Generator[Session, None, None]:
    """Get a requests HTTP session for making basic requests.

    Yields:
        :class:`~requests.Session`:
            A new clean session that plugins can use for requests.
    """

    with Session() as session:
        yield session


def get_soup(markup: str) -> BeautifulSoup:
    """Get a BeautifulSoup instance for some HTML markup.

    Args:
        markup (str):
            The HTML markup to use when building a BeautifulSoup instance.

    Returns:
        :class:`~bs4.BeautifulSoup`:
            The parsed soup for the given HTML markup.
    """

    return BeautifulSoup(markup=markup, features="lxml")
