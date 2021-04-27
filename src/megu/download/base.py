# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains the abstractions necessary to build content downloaders.

Attributes:
    DEFAULT_MAX_CONNECTIONS (int):
        The maximum number of connections permittable for a standard download.s
"""

import abc
from pathlib import Path
from typing import Any, Callable, Optional

from ..log import instance as log
from ..models import Content
from ..models.content import Manifest

DEFAULT_MAX_CONNECTIONS = 8


class BaseDownloader(abc.ABC):  # pragma: no cover
    """The base downloader that all content downloaders should inherit from."""

    @abc.abstractproperty
    def name(self) -> str:
        """Human readable name for the plugin."""

        raise NotADirectoryError(
            f"{self.__class__.__qualname__!s} must implement name property"
        )

    @abc.abstractclassmethod
    def can_handle(cls, content: Content) -> bool:
        """Check if some given content can be handled by the downloader.

        Args:
            content (~models.content.Content):
                The content to check against the current content.

        Returns:
            bool:
                True if the downloader can handle downloading the content,
                otherwise False
        """

        raise NotImplementedError(
            f"{cls.__class__.__qualname__!s} must implement can_handle classmethod"
        )

    @abc.abstractmethod
    def download_content(
        self,
        content: Content,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        update_hook: Optional[Callable[[int], Any]] = None,
    ) -> Manifest:
        """Download the resources of some content to temporary storage.

        Args:
            content (~models.content.Content):
                The content to download.
            max_connections (int, optional):
                The limit of connections to make to handle downloading the content.
                Defaults to :attr:`~DEFAULT_MAX_CONNECTIONS`.
            update_hook (Optional[Callable[[int], Any]], optional):
                Callable for reporting downloaded chunk sizes.
                Defaults to :data:`None`.

        Returns:
            ~models.content.Manifest:
                The manifest of downloaded content and local file artifacts.
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__!s} must implement download_content method"
        )
