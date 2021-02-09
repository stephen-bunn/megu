# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains definitions of content types used throughout the project."""

import abc
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from furl.furl import furl
from pydantic import AnyHttpUrl, BaseModel, Field

from ..hasher import HashType

Url = furl


class Checksum(BaseModel):
    """Describes a checksum that should be used for content validation."""

    type: HashType = Field(
        title="Type",
        description="The type of the checksum.",
    )
    hash: str = Field(
        title="Hash",
        description="The hex digest of the checksum.",
    )


class Meta(BaseModel):
    """Describes some additional metadata about the extracted content."""

    id: Optional[str] = Field(
        default=None,
        title="ID",
        description="The site's ID of the extracted content.",
    )
    title: Optional[str] = Field(
        default=None,
        title="Title",
        description="The site's title of the extracted content.",
    )
    description: Optional[str] = Field(
        default=None,
        title="Description",
        description="The site's description of the extracted content.",
    )
    publisher: Optional[str] = Field(
        default=None,
        title="Publisher",
        description="The username of the content's author.",
    )
    published_at: Optional[datetime] = Field(
        default=None,
        title="Published Datetime",
        description="The datetime the content was published on the site.",
    )
    duration: Optional[int] = Field(
        default=None,
        title="Duration",
        description="The duration in milliseconds of the content.",
    )
    filename: Optional[str] = Field(
        default=None,
        title="Filename",
        description="The file name of the content if available.",
    )
    thumbnail: Optional[AnyHttpUrl] = Field(
        default=None,
        title="Thumbnail",
        description="The HTTP URL for the content's thumbnail if available.",
    )


class Resource(abc.ABC, BaseModel):
    """The base resource class that resource types must inherit from."""

    @abc.abstractproperty
    def fingerprint(self) -> str:
        """Get the unique identifier of an resource.

        Raises:
            NotImplementedError:
                If a subclass simply calls ``super().fingerprint``.
                Subclasses must implement this property.

        Returns:
            str:
                A string fingerprint of the resource.
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__!s} must implement fingerprint property"
        )


class Content(BaseModel):
    """Describes some extracted content that can be downloaded."""

    class Config:
        """Configuration for Content model validation."""

        arbitrary_types_allowed = True

    id: str = Field(
        title="ID",
        descripion="The unique identifier of the content.",
        min_length=1,
    )
    url: AnyHttpUrl = Field(
        title="URL",
        description="The source URL the content was extracted from.",
    )
    quality: float = Field(
        title="Quality",
        description="The quality ranking of the content from the same URL.",
    )
    size: int = Field(
        title="Size",
        description="The size of the content in bytes.",
        gt=0,
    )
    type: str = Field(
        title="Type",
        description="The appropriate mimetype for the content.",
        min_length=1,
    )
    resources: List[Resource] = Field(
        title="Resources",
        description="The resources to fetch to recreate the remote content locally.",
        min_items=1,
    )
    meta: Meta = Field(
        default_factory=Meta,
        title="Meta",
        description="Meta container for traditional content metadata.",
    )
    checksums: List[Checksum] = Field(
        default_factory=list,
        title="Checksums",
        description="Checksum list if the fetched content can be validated.",
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        title="Extra",
        description="Container for miscellaneous content properties.",
    )

    @property
    def extension(self) -> Optional[str]:
        """File extension for the content.

        Returns:
            Optional[str]:
                The appropriate file extension for the content if discoverable.
        """

        return mimetypes.guess_extension(self.type)

    @property
    def filename(self) -> str:
        """Filename for the content.

        Returns:
            str:
                The appropriate filename for the content.
        """

        extension = self.extension
        return f"{self.id!s}{extension if extension else ''!s}"


class Manifest(BaseModel):
    """Describes the downloaded artifacts ready to be merged."""

    content: Content = Field(
        title="Content",
        description="The content responsible for the downloaded manifest.",
    )
    artifacts: List[Tuple[Resource, Path]] = Field(
        title="Artifacts",
        description="The list of pairs of downloaded resources and the artifact path.",
        min_items=1,
    )
