# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains definitions of types used throughout the project."""

import mimetypes
from datetime import datetime
from enum import Enum
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional

from cached_property import cached_property
from furl.furl import furl
from pydantic import AnyHttpUrl, BaseModel, Field
from requests import PreparedRequest
from requests.sessions import Request

from .hasher import HashType, hash_io
from .log import instance as log

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


class HTTPMethod(Enum):

    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    CONNECT = "CONNECT"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    PATCH = "PATCH"


class Artifact(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)

    method: HTTPMethod = Field(
        title="Method",
        description="HTTP Method to fetch the artifact URL.",
    )
    url: AnyHttpUrl = Field(
        title="URL",
        description="The artifact URL to fetch.",
    )
    headers: dict = Field(
        default_factory=dict,
        title="Headers",
        description="The headers to fetch the artifact URL.",
    )
    data: Optional[bytes] = Field(
        default=None,
        title="Data",
        description="The request data to fetch the artifact URL.",
    )
    auth: Optional[Callable[[Request], Request]] = Field(
        default=None,
        title="Authentication Handler",
        description="Callable to handle authenticating a request.",
    )

    def _get_signature(self) -> bytes:
        signature = bytes(
            "|".join((str(self.method.value), str(self.url), str(self.headers))),
            "utf-8",
        )

        if self.data is not None:
            signature += b"|" + self.data

        return signature

    @cached_property
    def fingerprint(self) -> str:
        fingerprint = hash_io(
            BytesIO(self._get_signature()),
            {HashType.XXHASH},
        )[HashType.XXHASH]
        log.debug(f"Computed fingerprint {fingerprint!r} for artifact {self!r}")

        return fingerprint

    @classmethod
    def from_request(cls, request: PreparedRequest) -> "Artifact":

        return Artifact(
            method=HTTPMethod(request.method or HTTPMethod.GET.value),
            url=request.url,
            headers=request.headers,
            data=request.body,
        )

    def to_request(self) -> PreparedRequest:
        return Request(
            method=self.method.value,
            url=self.url,
            headers=self.headers,
            data=self.data,
        ).prepare()


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
    artifacts: List[Artifact] = Field(
        title="Artifacts",
        description="The artifacts to fetch to recreate the remote content locally.",
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
        return mimetypes.guess_extension(self.type)
