# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains definitions of types used throughout the project."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from furl.furl import furl
from pydantic import AnyHttpUrl, BaseModel, Field
from requests import PreparedRequest

Url = furl


class ChecksumType(Enum):
    """Categorizes the different types of supported checksums."""

    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"
    CRC32 = "crc32"


class Checksum(BaseModel):
    """Describes a checksum that should be used for content validation."""

    type: ChecksumType = Field(
        title="Type",
        description="The type of the checksum.",
    )
    hash: str = Field(
        title="Hash",
        description="The hex digest of the checksum.",
    )


class Meta(BaseModel):
    """Describes some additional metadata about the extracted content."""

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
    requests: List[PreparedRequest] = Field(
        title="Requests",
        description="The requests to make to recreate the remote content locally.",
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
