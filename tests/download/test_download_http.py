from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, call, patch

import pytest
from httpx import Client, Response
from hypothesis import given
from hypothesis.strategies import lists

from megu.download.http import DEFAULT_CHUNK_SIZE, HTTPDownloader
from megu.models import URL, Content, HTTPResource

from ..strategies import content, http_resource


def test_HTTPDownloader_name():
    assert HTTPDownloader().name == "HTTP Downloader"


@given(content(resources_strat=lists(http_resource(), min_size=1, max_size=2)))
def test_HTTPDownloader_can_handle(content: Content):
    assert HTTPDownloader.can_handle(content) == True


def test_HTTPDownloader_session():
    assert isinstance(HTTPDownloader().session, Client)


def test_HTTPDownloader_session_uses_existing_session():
    downloader = HTTPDownloader()
    client = Client()
    downloader._session = client
    assert isinstance(downloader.session, Client)
    assert downloader.session == downloader._session


def test_HTTPDownloader_iter_ranges():
    assert list(HTTPDownloader()._iter_ranges(0, 10, 20, 5)) == [(0, 10), (11, 15), (16, 20)]


def test_HTTPDownloader_iter_ranges_raises_StopIteration_for_complete_range():
    with pytest.raises(StopIteration):
        next(HTTPDownloader()._iter_ranges(0, 10, 9))


def test_HTTPDownloader_request_resource(respx_mock, megu_url: URL):
    route = respx_mock.get(str(megu_url)).mock(return_value=Response(200))
    HTTPDownloader()._request_resource(HTTPResource("GET", megu_url))
    assert route.called == True


def test_HTTPDownloader_download_normal(respx_mock, megu_url: URL):
    resp = Response(200, content=b"test")
    respx_mock.get(str(megu_url)).mock(return_value=resp)

    with TemporaryDirectory() as temp_dir:
        temp_filepath = Path(temp_dir).joinpath("test")
        assert (
            HTTPDownloader()._download_normal(
                "test", HTTPResource("GET", megu_url), resp, temp_filepath
            )
            == temp_filepath
        )

        assert temp_filepath.stat().st_size == 4
        with temp_filepath.open("rb") as temp_io:
            assert temp_io.read() == b"test"


def test_HTTPDownloader_download_normal_calls_update_hook(respx_mock, megu_url: URL):
    resp = Response(200, content=b"test")
    respx_mock.get(str(megu_url)).mock(return_value=resp)
    update_hook_mock = MagicMock()

    with TemporaryDirectory() as temp_dir:
        HTTPDownloader()._download_normal(
            "test",
            HTTPResource("GET", megu_url),
            resp,
            Path(temp_dir).joinpath("test"),
            1,
            update_hook_mock,
        )

    update_hook_mock.assert_has_calls([call("test", 1, 4) for _ in range(4)])


def test_HTTPDownloader_download_partial(respx_mock, megu_url: URL):
    resp = Response(206, content=b"test", headers={"Content-Range": "bytes 1-4/4"})
    respx_mock.get(str(megu_url)).mock(return_value=resp)

    with TemporaryDirectory() as temp_dir:
        to_path = Path(temp_dir).joinpath("test")
        assert (
            HTTPDownloader()._download_partial("test", HTTPResource("GET", megu_url), resp, to_path)
            == to_path
        )

        with to_path.open("rb") as file_io:
            assert file_io.read() == b"test"


def test_HTTPDownloader_download_partial_fallback_for_missing_content_range(
    respx_mock, megu_url: URL
):
    resp = Response(206)
    respx_mock.get(str(megu_url)).mock(return_value=resp)

    downloader = HTTPDownloader()
    with TemporaryDirectory() as temp_dir, patch.object(
        downloader, "_download_normal"
    ) as mocked_download_normal:
        resource = HTTPResource("GET", megu_url)
        to_path = Path(temp_dir).joinpath("test")
        downloader._download_partial("test", resource, resp, to_path)

        mocked_download_normal.assert_has_calls(
            [call("test", resource, resp, to_path, chunk_size=DEFAULT_CHUNK_SIZE, update_hook=None)]
        )


def test_HTTPDownloader_download_partial_fallback_for_invalid_content_range(
    respx_mock, megu_url: URL
):
    resp = Response(206, headers={"Content-Range": "invalid"})
    respx_mock.get(str(megu_url)).mock(return_value=resp)

    downloader = HTTPDownloader()
    with TemporaryDirectory() as temp_dir, patch.object(
        downloader, "_download_normal"
    ) as mocked_download_normal:
        resource = HTTPResource("GET", megu_url)
        to_path = Path(temp_dir).joinpath("test")
        downloader._download_partial("test", resource, resp, to_path)

        mocked_download_normal.assert_has_calls(
            [call("test", resource, resp, to_path, chunk_size=DEFAULT_CHUNK_SIZE, update_hook=None)]
        )


def test_HTTPDownloader_download_partial_raises_ValueError_for_failing_range_iteration(
    respx_mock, megu_url: URL
):
    resp = Response(206, content=b"test", headers={"Content-Range": "bytes 4-1/*"})
    respx_mock.get(str(megu_url)).mock(return_value=resp)

    with TemporaryDirectory() as temp_dir, pytest.raises(ValueError) as error:
        HTTPDownloader()._download_partial(
            "test",
            HTTPResource("GET", megu_url),
            resp,
            Path(temp_dir).joinpath("test"),
        )

        assert "Iteration of ranges from" in str(error)


def test_HTTPDownloader_download_partial_calls_update_hook(respx_mock, megu_url: URL):
    resp = Response(206, content=b"test", headers={"Content-Range": "bytes 1-4/4"})
    respx_mock.get(str(megu_url)).mock(return_value=resp)
    update_hook_mock = MagicMock()

    with TemporaryDirectory() as temp_dir:
        HTTPDownloader()._download_partial(
            "test",
            HTTPResource("GET", megu_url),
            resp,
            Path(temp_dir).joinpath("test"),
            update_hook=update_hook_mock,
        )

    update_hook_mock.assert_has_calls([call("test", 4, 4)])


def test_HTTPDownloader_download_resource_for_status_200(respx_mock, megu_url: URL):
    resp = Response(200, content=b"test")
    respx_mock.get(str(megu_url)).mock(return_value=resp)
    downloader = HTTPDownloader()
    resource = HTTPResource("GET", megu_url)

    with TemporaryDirectory() as temp_dir, patch.object(
        downloader, "_download_normal"
    ) as mocked_download_normal, patch.object(
        downloader, "_request_resource"
    ) as mocked_request_resource:
        mocked_request_resource.return_value = resp
        temp_filepath = Path(temp_dir).joinpath("test")

        downloader._download_resource("test", resource, 1, temp_filepath)
        mocked_download_normal.assert_has_calls(
            [
                call(
                    "test",
                    resource,
                    resp,
                    temp_filepath,
                    chunk_size=DEFAULT_CHUNK_SIZE,
                    update_hook=None,
                )
            ]
        )


def test_HTTPDownloader_download_resource_for_status_206(respx_mock, megu_url: URL):
    resp = Response(206, content=b"test")
    respx_mock.get(str(megu_url)).mock(return_value=resp)
    downloader = HTTPDownloader()
    resource = HTTPResource("GET", megu_url)

    with TemporaryDirectory() as temp_dir, patch.object(
        downloader, "_download_partial"
    ) as mocked_download_partial, patch.object(
        downloader, "_request_resource"
    ) as mocked_request_resource:
        mocked_request_resource.return_value = resp
        temp_filepath = Path(temp_dir).joinpath("test")

        downloader._download_resource("test", resource, 1, temp_filepath)
        mocked_download_partial.assert_has_calls(
            [
                call(
                    "test",
                    resource,
                    resp,
                    temp_filepath,
                    chunk_size=DEFAULT_CHUNK_SIZE,
                    update_hook=None,
                )
            ]
        )


def test_HTTPDownloader_download_resource_raises_ValueError_for_invalid_resource(
    respx_mock, megu_url: URL
):
    respx_mock.get(str(megu_url)).mock(return_value=Response(404))
    with pytest.raises(ValueError) as error:
        resource = HTTPResource("GET", megu_url)
        HTTPDownloader()._download_resource("test", resource, 1, Path())
        assert f"Response for resource {resource} resolved to error 404" in str(error)


def test_HTTPDownloader_download_resource_raises_ValueError_for_empty_resource(
    respx_mock, megu_url: URL
):
    respx_mock.get(str(megu_url)).mock(return_value=Response(204))
    with pytest.raises(ValueError) as error:
        resource = HTTPResource("GET", megu_url)
        HTTPDownloader()._download_resource("test", resource, 1, Path())
        assert f"Response for resource {resource} has no content" in str(error)


def test_HTTPDownloader_download_resource_raises_ValueError_for_unhandled_status(
    respx_mock, megu_url: URL
):
    respx_mock.get(str(megu_url)).mock(return_value=Response(201))
    with pytest.raises(ValueError) as error:
        resource = HTTPResource("GET", megu_url)
        HTTPDownloader()._download_resource("test", resource, 1, Path())
        assert f"Response for resource {resource} resolved to unhandled status 201" in str(error)


def test_HTTPDownloader_download_content(respx_mock, megu_url: URL):
    respx_mock.get(str(megu_url)).mock(return_value=Response(200, content=b"test"))

    with TemporaryDirectory() as temp_dir:
        staging_dir = Path(temp_dir)
        content = Content(
            id="test",
            group="test",
            name="Test",
            quality=0,
            size=4,
            type="text/plain",
            url=megu_url,
            resources=[HTTPResource("GET", megu_url)],
        )
        assert HTTPDownloader().download_content(content, staging_dir,) == (
            "test",
            [
                (
                    "aa5e5419f63ab86fc7d73abcc622bee3",
                    staging_dir.joinpath(f"{content.id}.aa5e5419f63ab86fc7d73abcc622bee3"),
                )
            ],
        )
