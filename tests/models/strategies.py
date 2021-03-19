# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains custom hypothesis strategies for model testing."""

import string
from typing import Callable, Optional

from hypothesis.provisional import urls
from hypothesis.strategies import (
    SearchStrategy,
    binary,
    builds,
    composite,
    dictionaries,
    none,
    one_of,
    sampled_from,
    text,
)
from requests import Request

from megu.models.http import HttpMethod, HttpResource


@composite
def requests_request(
    draw,
    method_strategy: Optional[SearchStrategy[str]] = None,
    url_strategy: Optional[SearchStrategy[str]] = None,
    headers_strategy: Optional[SearchStrategy[dict]] = None,
) -> Request:
    """Composite strategy for building a basic requests Request instance."""

    return Request(
        method=draw(
            method_strategy
            if method_strategy
            else sampled_from(list(HttpMethod.__members__.keys()))
        ),
        url=draw(url_strategy if url_strategy else urls()),
        headers=draw(headers_strategy if headers_strategy else builds(dict)),
    )
