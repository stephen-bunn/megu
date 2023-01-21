from pathlib import Path
from tempfile import TemporaryDirectory, mkstemp
from typing import Iterator

import pytest
from httpx import Response
from hypothesis import assume, given
from hypothesis.strategies import just, lists, one_of

from megu.models import URL, Content, ContentManifest
from megu.plugin.generic import GenericPlugin

from ..strategies import content_manifest, content_manifest_artifact, path, url


def test_GenericPlugin_str():
    plugin = GenericPlugin()
    assert str(plugin) == "GenericPlugin(name='Generic Plugin', domains={'*'})"


@given(url())
def test_GenericPlugin_can_handle_everything(url: URL):
    plugin = GenericPlugin()
    assert plugin.can_handle(url) == True


def test_GenericPlugin_iter_content(respx_mock, megu_url: URL):
    plugin = GenericPlugin()
    route = respx_mock.head(str(megu_url)).mock(
        return_value=Response(200, headers={"Content-Length": "123", "Content-Type": "text/plain"})
    )

    content_iterator = plugin.iter_content(megu_url)
    assert isinstance(content_iterator, Iterator)
    content = next(content_iterator)
    assert route.called == True
    assert isinstance(content, Content)

    assert isinstance(content.id, str)
    assert content.name == "Generic Content"
    assert content.url == megu_url
    assert content.quality == 1
    assert content.size == 123
    assert content.type == "text/plain"

    assert len(content.resources) == 1
    resource = content.resources[0]
    assert resource.method == "GET"
    assert resource.url == megu_url


def test_GenericPlugin_iter_content_raises_StopIteration_for_invalid_url(respx_mock, megu_url: URL):
    plugin = GenericPlugin()
    respx_mock.head(str(megu_url)).mock(return_value=Response(404))

    content_iterator = plugin.iter_content(megu_url)
    assert isinstance(content_iterator, Iterator)

    with pytest.raises(StopIteration):
        next(content_iterator)


def test_GenericPlugin_write_content():
    with TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)
        to_path = temp_dirpath.joinpath("test")

        # create temporary file to act as an artifact
        # we should be safe to not cleanup this created temporary file as it is being created in the
        # temporary directory we are creating using the TemporarDirectory context manager
        _, temp_filename = mkstemp(dir=temp_dirpath)
        temp_filepath = Path(temp_filename)
        with temp_filepath.open("wb") as temp_io:
            temp_io.write(b"test")

        assert to_path.exists() == False
        GenericPlugin().write_content(("", [("", temp_filepath)]), to_path)
        assert to_path.is_file()

        # ensure content written to final path matches the artifact content
        with to_path.open("rb") as temp_io:
            assert temp_io.read() == b"test"


@given(
    content_manifest(
        artifacts_strat=one_of(
            just([]),
            lists(content_manifest_artifact(), min_size=2, max_size=4),
        )
    ),
    path(),
)
def test_GenericPlugin_write_content_raises_ValueError_for_multiple_artifacts(
    manifest: ContentManifest, to_path: Path
):
    _, artifacts = manifest
    with pytest.raises(ValueError) as error:
        GenericPlugin().write_content(manifest, to_path)

        assert f"Found {len(artifacts)} artifacts in manifest, GenericPlugin expects only 1" in str(
            error
        )


@given(
    content_manifest(artifacts_strat=lists(content_manifest_artifact(), min_size=1, max_size=1)),
    path(),
)
def test_GenericPlugin_write_content_raises_FileNotFoundError_for_missing_artifact(
    manifest: ContentManifest, to_path: Path
):
    _, artifacts = manifest
    _, artifact_path = artifacts[0]
    assume(artifact_path.exists() == False)

    with pytest.raises(FileNotFoundError) as error:
        GenericPlugin().write_content(manifest, to_path)
        assert f"No artifact file exists at {artifact_path}" in str(error)
