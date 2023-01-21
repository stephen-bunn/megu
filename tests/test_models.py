from hypothesis import given
from hypothesis.strategies import none, sampled_from

from megu.models import URL, Content, HTTPResource

from .strategies import content


def test_HTTPResource_fingerprint():
    resource = HTTPResource("GET", URL("https://example.org/"), headers={}, content=None)
    assert isinstance(resource.fingerprint, str)
    # Known fingerprint for the created resource
    assert resource.fingerprint == "c56b7c96f7f28ce751f1e3e0e16c86c2"


@given(content(extension_strat=sampled_from([".mp4", ".mp3", ".wav", ".mkv"])))
def test_Content_suffix_via_extension(content: Content):
    assert content.suffix == content.extension


@given(
    content(extension_strat=none(), type_strat=""),
    sampled_from(
        [
            ("video/mp4", ".mp4"),
            ("audio/mpeg", ".mp3"),
            ("audio/x-wav", ".wav"),
            # Here is one example of why its always better to NOT rely on mimetypes for extensions
            ("video/x-matroska", ".mpv"),
        ]
    ),
)
def test_Content_suffix_via_type(content: Content, expected: tuple[str, str]):
    mimetype, suffix = expected
    content.type = mimetype
    assert content.suffix == suffix


@given(content())
def test_Content_filename(content: Content):
    assert content.filename == f"{content.id}{content.suffix}"
