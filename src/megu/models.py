"""This module contains definitions for data descriptors.

These are the foundational building blocks of other parts of the library.
"""

from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from io import BytesIO
from mimetypes import guess_extension
from pathlib import Path
from typing import Any, Callable, Generator, TypeAlias

from httpx import URL, Request

from megu.hash import HashType, hash_io


class HttpResource(Request):
    """Describes an HTTP resource to fetch for some content."""

    def __signature(self) -> bytes:
        """Get the unique signature for the current instance.

        Returns:
            bytes: The unique signature given the current instance.
        """

        return bytes(
            "|".join(map(str, [self.method, self.headers, self.url, self.content])),
            "utf-8",
        )

    @cached_property
    def fingerprint(self) -> str:
        """The fingerprint of the current resource instance.

        Returns:
            str: The fingerprint of the current resource instance.
        """

        return hash_io(BytesIO(self.__signature()), {HashType.MD5})[HashType.MD5]


"""Describes all handled content resources."""
ContentResource: TypeAlias = HttpResource


@dataclass
class ContentChecksum:
    """Describes a checksum to validate some content.

    Args:
        type (str): The type of the checksum described in the value
        value (str): The value of the content checksum
    """

    type: str = field()
    value: str = field()


@dataclass
class ContentMetadata:
    """Describes some optional content metadata.

    All fields within this datatype _should_ remaing completely optional.

    Args:
        id (str | None, optional):
            The remote identifier of the content, Defaults to None.
        title (str | None, optional):
            The remote title of the content, Defaults to None.
        description (str | None, optional):
            The remote description of the content, Defaults to None.
        publisher (str | None, optional):
            The name of the publisher of the content, Defaults to None.
        published_at (datetime | None, optional):
            The time the content was published, Defaults to None.
        duration (int | None, optional):
            The duration of the content in milliseconds, Defaults to None.
        filename (str | None, optional):
            The remote filename of the content, Defaults to None.
        thumbnail (URL | None, optional):
            The URL of the content thumbnail, Defaults to None.
    """

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
    """Describes some content that can be downloaded.

    Args:
        id (str):
            The identifier of the content.
        name (str):
            The name of the variant of the content.
        quality (float):
            The relative quality of the content (larger is better).
        size (int):
            The size of the content in bytes.
        type (str):
            The mimetype of the content.
        url (URL):
            The source URL of the content.
        resources (list[ContentResource]):
            The list of resources to fetch to download the content.
        checksums (list[ContentChecksum], optional):
            The list of checksums to use for validating the downloaded content. Defaults to [].
        extension (str | None, optional):
            The known extension of the content. Defaults to None.
        extra (dict[str, Any], optional):
            Extra unstructured details about the content, Defaults to {}.
        metadata (ContentMetadata | None, optional):
            Additional content metadata discovered, Defaults to None.
    """

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
        """The best file suffix (extension) for the given content.

        Returns:
            str: The file suffix.
        """

        if self.extension is not None:
            return self.extension

        return guess_extension(self.type) or ""

    @property
    def filename(self) -> str:
        """The filename to use to store the content.

        Returns:
            str: The filename to use to store the content.
        """

        return f"{self.id}{self.suffix}"


"""Type describing a manifest of downloaded content artifacts to pass along to the plugin for
writing out to a single filepath.
"""
ContentManifest = tuple[str, list[tuple[str, Path]]]

"""Type describing the callable to use for filtering content."""
ContentFilter = Callable[[Generator[Content, None, None]], Generator[Content, None, None]]
