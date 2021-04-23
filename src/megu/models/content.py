# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains definitions of content types used throughout the project.

.. py:class:: Url

    A basic wrapper around a furl_ URL to keep things consistent between plugins and the
    internals of the package without declaring a direct dependency on a third-party.
"""

import abc
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ..hasher import HashType
from .types import Url


class Checksum(BaseModel):
    """Describes a checksum that should be used for content validation.

    Parameters:
        type (~hasher.HashType):
            The type of checksum hash is being defined.
        hash (str):
            The value of the checksum hash being defined.
        data (~typing.Dict, optional):
            Model parameter dictionary provided by pydantic.
            You should *likely* never use this property unless you need a keyword
            argument for a dictionary payload to construct the model.
    """

    type: HashType = Field(
        title="Type",
        description="The type of the checksum.",
    )
    hash: str = Field(
        title="Hash",
        description="The hex digest of the checksum.",
    )


class Meta(BaseModel):
    """Describes some additional metadata about the extracted content.

    Parameters:
        id (Optional[str], optional):
            The site internal identifier for the extracted content.
        title (Optional[str], optional):
            The site defined title for the extracted content.
        description (Optional[str], optional):
            The site defined description for the extracted content.
        publisher (Optional[str], optional):
            The site defined publisher name for the extracted content.
        published_at (Optional[~datetime.datetime], optional):
            The site defined datetime timestamp for when the extracted content was
            published.
        filename (Optional[str], optional):
            The site defined filename for the extracted content.
        thumbnail (Optional[str], optional):
            The URL for the thumbnail of the extracted content.
        data (~typing.Dict, optional):
            Model parameter dictionary provided by pydantic.
            You should *likely* never use this property unless you need a keyword
            argument for a dictionary payload to construct the model.
    """

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
    thumbnail: Optional[Url] = Field(
        default=None,
        title="Thumbnail",
        description="The HTTP URL for the content's thumbnail if available.",
    )


class Resource(abc.ABC, BaseModel):
    """The base resource class that resource types must inherit from.

    .. important::
        This class is abstract and used as an typing interface for the
        :class:`~megu.models.content.Content` model.
        Concrete implementations of this abstract class such as
        :class:`~megu.models.http.HttpResource` must be provided to content in order
        for the application to understand how to fetch the content.

    Parameters:
        data (~typing.Dict, optional):
            You should never use this parameter.
            Since this is an abstract class, you should never be instantiating it.
    """

    @abc.abstractproperty
    def fingerprint(self) -> str:  # pragma: no cover
        """Get the unique identifier of an resource.

        Raises:
            NotImplementedError:
                Subclasses must implement this property.

        Returns:
            str:
                A string fingerprint of the resource.
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__!s} must implement fingerprint property"
        )


class Content(BaseModel):
    """Describes some extracted content that can be downloaded.

    Parameters:
        id (str):
            The plugin-defined content-unique identifier for the content.
        url (str):
            The absolute URL from where the plugin extracted the content.
            This URL string gets translated into a :class:`~megu.models.types.Url`
            instance.
        quality (float):
            The plugin-defined arbitrary quality of the content.
        size (int):
            The size in bytes the content will take up on the local filesystem.
        type (str):
            The appropriate mimetype of the content.
        resources (List[~megu.models.content.Resource]):
            The resources required to fetch and download the extracted content.
        meta (~megu.models.content.Meta):
            The structured metadata of the extracted content.
        checksums (List[~megu.models.content.Checksum]):
            A list of checksums that can be used to verify the downloaded content.
        extra (Dict[str, ~typing.Any):
            The unstructured metadata of the extracted content.
        data (~typing.Dict, optional):
            Model parameter dictionary provided by pydantic.
            You should *likely* never use this property unless you need a keyword
            argument for a dictionary payload to construct the model.
    """

    class Config:
        """Configuration for Content model validation."""

        arbitrary_types_allowed = True

    id: str = Field(
        title="ID",
        descripion="The unique identifier of the content.",
        min_length=1,
    )
    url: Url = Field(
        title="URL",
        description="The source URL the content was extracted from.",
    )
    quality: float = Field(
        title="Quality",
        description="The quality ranking of the content from the same URL.",
        ge=0,
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
    extension: Optional[str] = Field(
        title="Extension",
        description="The appropriate file extension for the content.",
        regex=r"^\..+$",
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
    def ext(self) -> str:
        """File extension for the content.

        Returns:
            str:
                The best suitable file extension for the content.
                May be a blank string if a extension cannot be determined.
        """

        if self.extension is not None:
            return self.extension

        return mimetypes.guess_extension(self.type) or ""

    @property
    def filename(self) -> str:
        """Filename for the content.

        Returns:
            str:
                The appropriate filename for the content.
        """

        return f"{self.id!s}{self.ext!s}"


class Manifest(BaseModel):
    """Describes the downloaded artifacts ready to be merged.

    Parameters:
        content (~models.content.Content):
            The content instance that was download.
        artifacts (List[Tuple[~models.content.Resource, ~pathlib.Path]]):
            A tuple containing (resource, path) of content resources that were
            downloaded to the local filesystem.
        data (~typing.Dict, optional):
            Model parameter dictionary provided by pydantic.
            You should *likely* never use this property unless you need a keyword
            argument for a dictionary payload to construct the model.
    """

    content: Content = Field(
        title="Content",
        description="The content responsible for the downloaded manifest.",
    )
    artifacts: List[Tuple[Resource, Path]] = Field(
        title="Artifacts",
        description="The list of pairs of downloaded resources and the artifact path.",
        min_items=1,
    )
