# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for the Http downloader."""

from typing import Iterator
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis.strategies import booleans, integers, lists
from requests import PreparedRequest, Session

from megu.download.http import HttpDownloader
from megu.models.content import Content
from megu.models.http import HttpResource

from ..strategies import megu_content, megu_http_resource


def test_session():
    downloader = HttpDownloader()
    session = downloader.session
    assert isinstance(session, Session)
    assert downloader.session is session


@given(
    megu_content(resources_strategy=lists(megu_http_resource(), min_size=1, max_size=3))
)
def test_can_handle(content: Content):
    assert HttpDownloader.can_handle(content) == True


@given(megu_http_resource(), booleans())
def test_request_resource(resource: HttpResource, stream: bool):
    downloader = HttpDownloader()

    with patch.object(downloader, "session") as mocked_session:
        downloader._request_resource(resource, stream=stream)
        send_call = mocked_session.send.call_args

        assert isinstance(send_call.args[0], PreparedRequest)
        assert send_call.kwargs["stream"] == stream


@given(
    integers(min_value=0, max_value=1024),
    integers(min_value=1024, max_value=2048),
    integers(min_value=2048, max_value=4096),
)
def test_iter_range(start: int, end: int, size: int):
    downloader = HttpDownloader()

    iterator = downloader._iter_ranges(start, end, size=size)
    assert isinstance(iterator, Iterator)

    first_start = None
    last_end = None
    for chunk_start, chunk_end in iterator:
        if first_start is None:
            first_start = chunk_start
        last_end = chunk_end

        assert chunk_end >= chunk_start

    assert first_start == start
    assert last_end == size


@given(
    integers(min_value=0, max_value=1024),
    integers(min_value=1024, max_value=1025),
    integers(min_value=0, max_value=1024),
)
def test_iter_range_raises_StopIteration(start: int, end: int, size: int):
    downloader = HttpDownloader()
    with pytest.raises(StopIteration):
        next(downloader._iter_ranges(start, end, size=size))
