# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains definitions of HTTP resource types used throughout the project."""

from __future__ import annotations

from enum import Enum
from io import BytesIO
from typing import Callable, Optional

from cached_property import cached_property
from pydantic import AnyHttpUrl, Field
from requests import PreparedRequest
from requests.sessions import Request

from ..hasher import HashType, hash_io
from ..log import instance as log
from .content import Resource


class HttpMethod(Enum):
    """Enumeration of the available HTTP methods that resources can use."""

    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    CONNECT = "CONNECT"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    PATCH = "PATCH"


class HttpResource(Resource):
    """Describes a downloadable HTTP resource that is part of some local content."""

    class Config:
        """Model configuration for the Resource model."""

        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)

    method: HttpMethod = Field(
        title="Method",
        description="HTTP Method to fetch the resource URL.",
    )
    url: AnyHttpUrl = Field(
        title="URL",
        description="The resource URL to fetch.",
    )
    headers: dict = Field(
        default_factory=dict,
        title="Headers",
        description="The headers to fetch the resource URL.",
    )
    data: Optional[bytes] = Field(
        default=None,
        title="Data",
        description="The request data to fetch the resource URL.",
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
        """Get a computed unique identifier for the resource.

        Returns:
            str:
                The unique identifier for the resource.
        """

        fingerprint = hash_io(
            BytesIO(self._get_signature()),
            {HashType.XXHASH},
        )[HashType.XXHASH]
        log.debug(f"Computed fingerprint {fingerprint!r} for resource {self!r}")

        return fingerprint

    @classmethod
    def from_request(cls, request: PreparedRequest) -> HttpResource:
        """Produce an resource from an existing prepared request.

        Args:
            request (:class:`~requests.PreparedRequest`):
                The request to construct an resource from.

        Returns:
            :class:`~types.HTTPResource`:
                The newly produced resource.
        """

        return HttpResource(
            method=HttpMethod(request.method or HttpMethod.GET.value),
            url=request.url,
            headers=request.headers,
            data=request.body,
        )

    def to_request(self) -> PreparedRequest:
        """Get a matching prepared request for the current resource.

        Returns:
            :class:`~requests.PreparedRequest`:
                The matching prepared request for the current resource.
        """

        return Request(
            method=self.method.value,
            url=self.url,
            headers=self.headers,
            data=self.data,
        ).prepare()
