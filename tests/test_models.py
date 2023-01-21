from hypothesis import given
from hypothesis.strategies import none

from megu.models import URL, Content, HTTPResource

from .strategies import content


def test_HTTPResource_fingerprint():
    resource = HTTPResource("GET", URL("https://example.org/"), headers={}, content=None)
    assert isinstance(resource.fingerprint, str)
    assert resource.fingerprint == "c56b7c96f7f28ce751f1e3e0e16c86c2"


@given(content(extension_strat=".mp4"))
def test_Content_suffix_via_extension(content: Content):
    assert content.suffix == ".mp4"


@given(content(extension_strat=none(), type_strat="video/mp4"))
def test_Content_suffix_via_type(content: Content):
    assert content.suffix == ".mp4"


@given(content())
def test_Content_filename(content: Content):
    assert content.filename == f"{content.id}{content.suffix}"
