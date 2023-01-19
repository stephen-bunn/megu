from io import BytesIO
from typing import Generator
from pathlib import Path

from megu.plugin.base import BasePlugin
from megu.models import URL, Content, ContentManifest, HttpResource
from megu.hash import hash_io, HashType
from megu.helpers import http_session


class GenericPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "Generic Plugin"

    @property
    def domains(self) -> set[str]:
        return {"*"}

    @staticmethod
    def __build_content_id(url: URL) -> str:
        url_hash = hash_io(BytesIO(bytes(str(url), "utf-8")), {HashType.MD5})[HashType.MD5]
        return f"generic-{url_hash}"

    @classmethod
    def can_handle(cls, url: URL) -> bool:
        return True

    def iter_content(self, url: URL) -> Generator[Content, None, None]:
        with http_session() as session:
            head = session.head(url)
            if not head.is_success:
                return

            yield Content(
                id=GenericPlugin.__build_content_id(url),
                name="Generic Content",
                url=url,
                quality=1,
                size=int(head.headers.get("Content-Length", 0)),
                type=head.headers.get("Content-Type", "application/octet-stream"),
                resources=[HttpResource(method="GET", url=url)],
            )

    def write_content(self, manifest: ContentManifest, to_path: Path) -> Path:
        _, artifacts = manifest
        if len(artifacts) != 1:
            raise ValueError(
                f"Found {len(artifacts)} artifacts in manifest, "
                f"{self.__class__.__qualname__} expects only 1"
            )

        _, artifact_path = artifacts[0]
        if not artifact_path.is_file():
            raise FileNotFoundError(f"No artifact file at {artifact_path} exists")

        return artifact_path.rename(to_path)
