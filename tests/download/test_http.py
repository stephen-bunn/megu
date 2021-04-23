# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for the Http downloader."""

import platform
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
    sampled_from,
    text,
)
from requests import PreparedRequest, Response, Session

from megu.download.http import CONTENT_RANGE_PATTERN, HttpDownloader
from megu.models.content import Content
from megu.models.http import HttpResource

from ..strategies import (
    megu_content,
    megu_http_resource,
    pathlib_path,
    requests_response,
)


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


@pytest.mark.skipif(
    platform.system().lower() == "windows",
    reason="Github Actions CI does not have access to temporary diretory for Windows",
)
@given(
    megu_http_resource(),
    requests_response(
        status_code_strategy=just(200),
        headers_strategy=one_of(
            dictionaries(
                keys=just("Content-Length"),
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


@pytest.mark.skipif(
    platform.system().lower() == "windows",
    reason="Github Actions CI does not have access to temporary diretory for Windows",
)
@given(
    megu_http_resource(),
    requests_response(
        headers_strategy=dictionaries(
            keys=just("content-range"),
            values=just("bytes 0-256/512"),
            min_size=1,
            max_size=1,
        ),
        raw_strategy=binary(min_size=256, max_size=256),
    ),
    requests_response(
        headers_strategy=dictionaries(
            keys=just("content-range"),
            values=just("bytes 257-512/512"),
            min_size=1,
            max_size=1,
        ),
        raw_strategy=binary(min_size=255, max_size=255),
    ),
    integers(min_value=1, max_value=256),
    one_of(builds(MagicMock), none()),
)
def test_download_partial(
    resource: HttpResource,
    response: Response,
    second_response: Response,
    chunk_size: int,
    update_hook: Optional[MagicMock],
):
    downloader = HttpDownloader()
    with patch(
        "megu.download.http.allocate_storage"
    ) as mock_allocate_storage, patch.object(
        downloader, "_request_resource"
    ) as mock_request_resource, NamedTemporaryFile() as temp_file:
        mock_request_resource.return_value = second_response
        to_path = Path(temp_file.name)
        result = downloader._download_partial(
            resource, response, to_path, chunk_size=chunk_size, update_hook=update_hook
        )

        mock_allocate_storage.assert_called_once_with(to_path, 512)

        if update_hook is not None:
            update_hook.assert_has_calls([call(chunk_size)])

        assert result == to_path

        # check downloaded content from stream is expected
        temp_file.seek(0)
        assert temp_file.read() == response.content + second_response.content


@given(
    megu_http_resource(),
    requests_response(
        headers_strategy=one_of(
            builds(dict),
            dictionaries(
                keys=just("content-range"),
                values=one_of(
                    text().filter(
                        lambda value: CONTENT_RANGE_PATTERN.match(value) is None
                    ),
                    just("bytes 0-*/*"),
                ),
                min_size=1,
                max_size=1,
            ),
        )
    ),
    pathlib_path(),
    integers(min_value=1, max_value=256),
    one_of(builds(MagicMock), none()),
)
def test_download_partial_fallback(
    resource: HttpResource,
    response: Response,
    to_path: Path,
    chunk_size: int,
    update_hook: Optional[MagicMock],
):
    downloader = HttpDownloader()
    with patch.object(downloader, "_download_normal") as mock_download_normal:
        downloader._download_partial(
            resource, response, to_path, chunk_size=chunk_size, update_hook=update_hook
        )

        mock_download_normal.assert_called_once_with(
            resource, response, to_path, chunk_size=chunk_size, update_hook=update_hook
        )


@given(
    megu_http_resource(),
    pathlib_path(),
    integers(1, 1024),
    requests_response(status_code_strategy=sampled_from([200, 206])),
)
def test_download_resource_download_normal(
    resource: HttpResource,
    to_path: Path,
    chunk_size: int,
    response: Response,
):
    downloader = HttpDownloader()
    with patch.object(
        downloader, "_request_resource"
    ) as mock_request_resource, patch.object(
        downloader, "_download_normal"
    ) as mock_download_normal, patch.object(
        downloader, "_download_partial"
    ) as mock_download_partial:
        mock_request_resource.return_value = response

        mock_update_hook = MagicMock()
        downloader.download_resource(
            resource,
            0,
            to_path,
            chunk_size=chunk_size,
            update_hook=mock_update_hook,
        )

        download_mock = (
            mock_download_normal
            if response.status_code == 200
            else mock_download_partial
        )
        download_mock.assert_called_once_with(
            resource,
            response,
            to_path,
            chunk_size=chunk_size,
            update_hook=mock_update_hook,
        )


@given(
    megu_http_resource(),
    pathlib_path(),
    requests_response(status_code_strategy=sampled_from([300, 204, 400])),
)
def test_download_resource_raises_ValueError(
    resource: HttpResource, to_path: Path, response: Response
):
    downloader = HttpDownloader()
    with patch.object(downloader, "_request_resource") as mock_request_resource:
        mock_request_resource.return_value = response

        with pytest.raises(ValueError):
            downloader.download_resource(resource, 0, to_path)


@given(
    megu_content(),
    requests_response(
        headers_strategy=dictionaries(
            keys=just("Content-Length"),
            values=integers(min_value=1, max_value=1024),
            min_size=1,
            max_size=1,
        )
    ),
)
def test_get_content_size(content: Content, response: Response):
    downloader = HttpDownloader()
    with patch.object(downloader.session, "head") as mock_session_head:
        mock_session_head.return_value = response
        content_size = downloader._get_content_size(content)

        assert content_size > 0
