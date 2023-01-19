from io import BytesIO
from mimetypes import guess_extension
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeAlias
from pathlib import Path
from functools import cached_property

from httpx import URL, Request

from megu.hash import hash_io, HashType


class HttpResource(Request):
    def __signature(self) -> bytes:
        return bytes(
            "|".join(map(str, [self.method, self.headers, self.url, self.content])),
            "utf-8",
        )

    @cached_property
    def fingerprint(self) -> str:
        return hash_io(BytesIO(self.__signature()), {HashType.MD5})[HashType.MD5]


ContentResource: TypeAlias = HttpResource


@dataclass
class ContentChecksum:
    type: str = field()
    value: str = field()


@dataclass
class ContentMetadata:
    id: str | None = field(default=None)
    title: str | None = field(default=None)
    description: str | None = field(default=None)
    publisher: str | None = field(default=None)
    published_at: datetime | None = field(default=None)
    duration: int | None = field(default=None)
    filename: str | None = field(default=None)
    thumbnail: URL | None = field(default=None)


@dataclass
class Content:
    id: str = field()
    name: str = field()
    quality: float = field()
    size: int = field()
    type: str = field()
    url: URL = field()
    resources: list[ContentResource] = field()

    checksums: list[ContentChecksum] = field(default_factory=list)
    extension: str | None = field(default=None)
    extra: dict[str, Any] = field(default_factory=dict)
    metadata: ContentMetadata | None = field(default=None)

    @property
    def suffix(self) -> str:
        if self.extension is not None:
            return self.extension

        return guess_extension(self.type) or ""

    @property
    def filename(self) -> str:
        return f"{self.id}{self.suffix}"


ContentManifest = tuple[str, list[tuple[str, Path]]]
