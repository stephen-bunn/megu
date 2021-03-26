# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for the Http downloader."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator, Optional
from unittest.mock import MagicMock, call, patch

import pytest
from hypothesis import given
from hypothesis.strategies import (
    binary,
    booleans,
    builds,
    dictionaries,
    integers,
    just,
    lists,
    none,
    one_of,
)
from requests import PreparedRequest, Response, Session

from megu.download.http import HttpDownloader
from megu.models.content import Content
from megu.models.http import HttpResource

from ..strategies import megu_content, megu_http_resource, requests_response


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
    integers(min_value=1025, max_value=2048),
    integers(min_value=0, max_value=1024),
)
def test_iter_range_raises_StopIteration(start: int, end: int, size: int):
    downloader = HttpDownloader()
    with pytest.raises(StopIteration):
        next(downloader._iter_ranges(start, end, size=size))


@given(
    megu_http_resource(),
    requests_response(
        status_code_strategy=just(200),
        headers_strategy=one_of(
            dictionaries(
                keys=just("content-length"),
                values=integers(min_value=1, max_value=1024),
                min_size=1,
                max_size=1,
            ),
            builds(dict),
        ),
        raw_strategy=binary(min_size=1024, max_size=2048),
    ),
    integers(min_value=1, max_value=256),
    one_of(builds(MagicMock), none()),
)
def test_download_normal(
    resource: HttpResource,
    response: Response,
    chunk_size: int,
    update_hook: Optional[MagicMock],
):
    downloader = HttpDownloader()
    with patch(
        "megu.download.http.allocate_storage"
    ) as mock_allocate_storage, NamedTemporaryFile() as temp_file:
        to_path = Path(temp_file.name)
        result = downloader._download_normal(
            resource,
            response,
            to_path,
            chunk_size=chunk_size,
            update_hook=update_hook,
        )

        if "content-length" in response.headers:
            mock_allocate_storage.assert_called_once_with(
                to_path, response.headers["content-length"]
            )

        if update_hook is not None:
            update_hook.assert_has_calls([call(chunk_size)])

        assert result == to_path

        # check downloaded content from stream is expected
        temp_file.seek(0)
        assert temp_file.read() == response.content
