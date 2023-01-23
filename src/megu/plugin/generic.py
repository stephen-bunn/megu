"""This module contains the definition of a generic plugin that assumes it can handle everything."""

from io import BytesIO
from pathlib import Path
from typing import Generator

from megu.hash import HashType, hash_io
from megu.helpers import http_session
from megu.models import URL, Content, ContentManifest, HTTPResource
from megu.plugin.base import BasePlugin


class GenericPlugin(BasePlugin):
    """Generic plugin that assumes it can handle any URL provided to it."""

    @property
    def name(self) -> str:
        """The name of the plugin."""

        return "Generic Plugin"

    @property
    def domains(self) -> set[str]:
        """The handled domains of the plugin."""

        return {"*"}

    @staticmethod
    def __build_content_id(url: URL) -> str:
        """Construct the unique content id for the given URL.

        Args:
            url (URL): The URL to get the unique content ID for.

        Returns:
            str: The unique content ID of the given URL.
        """

        url_hash = hash_io(BytesIO(bytes(str(url), "utf-8")), {HashType.MD5})[HashType.MD5]
        return f"generic-{url_hash}"

    @classmethod
    def can_handle(cls, url: URL) -> bool:
        """Determine if the generic plugin can handle the given URL.

        Always returns `True`.

        Args:
            url (URL): The URL that the generic plugin can handle.

        Returns:
            bool: True
        """

        return True

    def iter_content(self, url: URL) -> Generator[Content, None, None]:
        """Iterate over content discovered at the given URL.

        Args:
            url (URL): The URL to discover content from.

        Yields:
            Content: Discovered content from the given URL.
        """

        with http_session() as session:
            head = session.head(url)
            if not head.is_success:
                return

            content_id = GenericPlugin.__build_content_id(url)
            yield Content(
                id=content_id,
                group=content_id,
                name="Generic Content",
                url=url,
                quality=1,
                size=int(head.headers.get("Content-Length", 0)),
                type=head.headers.get("Content-Type", "application/octet-stream"),
                resources=[HTTPResource(method="GET", url=url)],
            )

    def write_content(self, manifest: ContentManifest, to_path: Path) -> Path:
        """Write content artifacts from the manifest to a given filepath.

        Args:
            manifest (ContentManifest): The content manifest containing downloaded artifacts.
            to_path (Path): The filepath to write the content to.

        Raises:
            ValueError: If the length of artifacts in the manifest is not exactly 1.
            FileNotFoundError: If any of the artifacts in the manifest does not exist.

        Returns:
            Path: The filepath that content was written to.
        """

        _, artifacts = manifest
        if len(artifacts) != 1:
            raise ValueError(
                f"Found {len(artifacts)} artifacts in manifest, "
                f"{self.__class__.__qualname__} expects only 1"
            )

        _, artifact_path = artifacts[0]
        if not artifact_path.is_file():
            raise FileNotFoundError(f"No artifact file exists at {artifact_path}")

        return artifact_path.rename(to_path)
