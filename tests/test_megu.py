from hypothesis import given
from hypothesis.strategies import one_of

from megu import normalize_url
from megu.models import URL

from .strategies import DEFAULT_URL_STRAT, url


@given(one_of(url(), DEFAULT_URL_STRAT))
def test_normalize_url(url: str | URL):
    normalized = normalize_url(url)
    assert isinstance(normalized, URL)


def test_get_plugin():
    ...


def test_get_plugin_ignores_urls_not_matching_supported_domains():
    ...


def test_get_plugin_ignores_unhandled_urls():
    ...


def test_get_plugin_returns_GenericPlugin_for_none_found():
    ...


def test_iter_content():
    ...


def test_write_content():
    ...


def test_write_content_raises_FileExistsError_for_existing_output_file():
    ...


def test_get_downloader():
    ...


def test_get_downloader_raises_ValueError_for_unhandled_downloads():
    ...


def test_download():
    ...


def test_download_raises_NotADirectoryError_for_missing_directory():
    ...


def test_download_raises_FileExistsError_for_existing_output_file():
    ...
