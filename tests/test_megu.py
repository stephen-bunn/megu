from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from httpx import Response
from hypothesis import assume, given
from hypothesis.strategies import lists, one_of

from megu import fetch, get_downloader, get_plugin, iter_content, normalize_url, write_content
from megu.download.http import HTTPDownloader
from megu.models import URL, Content, ContentManifest
from megu.plugin.generic import GenericPlugin

from .strategies import DEFAULT_URL_STRAT, content, content_manifest, http_resource, path, url


@given(one_of(url(), DEFAULT_URL_STRAT))
def test_normalize_url(url: str | URL):
    normalized = normalize_url(url)
    assert isinstance(normalized, URL)


@given(url())
def test_get_plugin(url: URL):
    class TestPlugin:
        domains = {"*"}

        @classmethod
        def can_handle(cls, url: URL) -> bool:
            return True

    with patch("megu.iter_plugins", lambda *args, **kwargs: iter([("test", [TestPlugin])])):
        assert isinstance(get_plugin(url), TestPlugin)


@given(url())
def test_get_plugin_ignores_urls_not_matching_supported_domains(url: URL):
    class TestPlugin:
        domains = {""}

        @classmethod
        def can_handle(cls, url: URL) -> bool:
            return True

    with patch("megu.iter_plugins", lambda *args, **kwargs: iter([("test", [TestPlugin])])):
        assert isinstance(get_plugin(url), GenericPlugin)


@given(url())
def test_get_plugin_ignores_unhandled_urls(url: URL):
    class TestPlugin:
        domains = {"*"}

        @classmethod
        def can_handle(cls, url: URL) -> bool:
            return False

    with patch("megu.iter_plugins", lambda *args, **kwargs: iter([("test", [TestPlugin])])):
        assert isinstance(get_plugin(url), GenericPlugin)


@given(url())
def test_get_plugin_returns_GenericPlugin_for_none_found(url: URL):
    assert isinstance(get_plugin(url), GenericPlugin)


@given(url(), content())
def test_iter_content(url: URL, content: Content):
    class TestPlugin:
        def iter_content(self, url: URL):
            yield content

    assert next(iter_content(TestPlugin(), url)) == content  # type: ignore


def test_write_content():
    with TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)
        artifact_filepath = temp_dirpath.joinpath("artifact")
        to_path = temp_dirpath.joinpath("test")

        with artifact_filepath.open("wb") as artifact_io:
            artifact_io.write(b"test")

        assert (
            write_content(GenericPlugin(), ("test", [("test", artifact_filepath)]), to_path)
            == to_path
        )

        with to_path.open("rb") as file_io:
            assert file_io.read() == b"test"


@given(content_manifest())
def test_write_content_raises_FileExistsError_for_existing_output_file(manifest: ContentManifest):
    with TemporaryDirectory() as temp_dir:
        to_path = Path(temp_dir).joinpath("test")
        to_path.touch()

        with pytest.raises(FileExistsError) as error:
            write_content(GenericPlugin(), manifest, to_path)
            assert f"File already exists at {to_path}" in str(error)


@given(content(resources_strat=lists(http_resource(), min_size=1, max_size=2)))
def test_get_downloader(content: Content):
    assert isinstance(get_downloader(content), HTTPDownloader)


@given(content())
def test_get_downloader_raises_ValueError_for_unhandled_downloads(content: Content):
    with patch("megu.iter_downloaders", lambda *args, **kwargs: iter([])), pytest.raises(
        ValueError
    ) as error:
        get_downloader(content)
        assert f"Failed to find a downloader that can handle content {content}" in str(error)


def test_fetch(respx_mock, megu_url: URL):
    respx_mock.head(str(megu_url)).mock(
        return_value=Response(200, headers={"Content-Length": "4", "Content-Type": "text/plain"})
    )
    respx_mock.get(str(megu_url)).mock(return_value=Response(200, content=b"test"))

    with TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)
        to_path = next(fetch(megu_url, temp_dirpath))
        assert to_path == temp_dirpath.joinpath("generic-3c76cc1eef59aaa8725f79f7e845395c.txt")
        with to_path.open("rb") as file_io:
            assert file_io.read() == b"test"


@given(url(), path())
def test_fetch_raises_NotADirectoryError_for_missing_directory(url: URL, path: Path):
    assume(path.exists() == False)
    with pytest.raises(NotADirectoryError) as error:
        next(fetch(url, path))
        assert f"No directory exists at {path}" in str(error)
