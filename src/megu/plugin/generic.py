# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains a very generic fallback plugin."""

from io import BytesIO
from pathlib import Path
from typing import Generator, Literal

from ..hasher import HashType, hash_io
from ..helpers import http_session
from ..log import instance as log
from ..models import Content, HttpMethod, HttpResource, Manifest, Url
from .base import BasePlugin


class GenericPlugin(BasePlugin):
    """A very generic fallback plugin.

    This plugin assumes that the given URL can just be downloaded with a single
    HTTP Get request and that it produces a single artifact that only needs to be
    renamed.
    """

    name = "Generic Plugin"
    domains = {"*"}  # this domain should really never be checked against

    @staticmethod
    def _build_id(url: Url) -> str:
        """Produce an content id for the provided Url.

        Args:
            url (~megu.models.content.Url):
                The Url instance to build a content id for.

        Returns:
            str:
                The appropriate generic content id for the given Url.
        """

        url_hash = hash_io(
            BytesIO(bytes(url.url, "utf-8")),
            {HashType.XXHASH},
        )[HashType.XXHASH]

        return f"generic-{url_hash!s}"

    def can_handle(self, url: Url) -> Literal[True]:
        """Check if the plugin can handle the given URL.

        Args:
            url (~megu.models.content.Url):
                The URL to check against the generic plugin.

        Returns:
            Literal[:data:`True`]:
                This plugin assumes it can handle any URL,
                therefore it always returns True.
        """

        return True

    def extract_content(self, url: Url) -> Generator[Content, None, None]:
        """Extract the content from the given Url instance.

        This extraction makes a single HTTP Head request to fetch Content-Length and
        Content-Type. Otherwise, it returns a single content instance based on the hash
        of the given Url.

        Args:
            url (~megu.models.content.Url):
                The URL to extract content from.

        Yields:
            Generator[:class:`~megu.models.content.Content`, None, None]:
                The extracted content from the given Url instance.
        """

        with http_session() as session:
            log.debug(f"Requesting HEAD details from {url.url!r}")
            head = session.head(url.url)

            yield Content(
                id=GenericPlugin._build_id(url),
                url=url.url,
                quality=1.0,
                size=int(head.headers["Content-Length"]),
                type=head.headers["Content-Type"],
                resources=[HttpResource(method=HttpMethod.GET, url=url.url)],
            )

    def merge_manifest(self, manifest: Manifest, to_path: Path) -> Path:
        """Merge the given manifest artifacts into a single filepath.

        Args:
            manifest (~megu.models.content.Manifest):
                The manifest of the downloaded artifacts.
            to_path (~pathlib.Path):
                The path that the artifacts should be merged into.

        Raises:
            ValueError:
                When the provided manifest contains more than 1 artifact.

        Returns:
            ~pathlib.Path:
                The filepath the artifacts were merged into.
        """

        if len(manifest.artifacts) != 1:
            raise ValueError(
                f"Found {len(manifest.artifacts)} artifacts in manifest, "
                f"{self.__class__.__qualname__!s} expects only 1"
            )

        log.debug(f"Merging artifacts from {manifest!r} to {to_path.as_posix()!r}")
        _, artifact_path = manifest.artifacts[0]
        artifact_path.rename(to_path)

        return to_path
