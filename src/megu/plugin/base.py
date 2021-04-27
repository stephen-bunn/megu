# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains the abstractions necessary for the plugin discovery to work."""

import abc
from pathlib import Path
from typing import Generator, Set

from ..models import Content, Manifest, Url


class BasePlugin(abc.ABC):  # pragma: no cover
    """The base plugin that all plugins should inherit from.

    This class should mostly be excluded from testing as it should only ever define an
    interface and not provide much if any implementation.
    """

    def __str__(self) -> str:
        """Build a human-friendly string representation of a plugin.

        Returns:
            str:
                The human-friendly string representation of a plugin.
        """

        return (
            f"{self.__class__.__qualname__!s}"
            f"(name={self.name!r}, domains={self.domains!r})"
        )

    @abc.abstractproperty
    def name(self) -> str:
        """Human readable name for the plugin."""

        raise NotImplementedError(
            f"{self.__class__.__qualname__!s} must implement name property"
        )

    @abc.abstractproperty
    def domains(self) -> Set[str]:
        """Set of domains that this plugin supports."""

        raise NotImplementedError(
            f"{self.__class__.__qualname__!s} must implement domains property"
        )

    @abc.abstractmethod
    def can_handle(self, url: Url) -> bool:
        """Check if a given Url can be handled by the plugin.

        Args:
            url (~megu.models.content.Url):
                The URL to check against the current plugin.

        Returns:
            bool:
                True if the plugin can handle the given URL, otherwise False
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__!s} must implement can_handle method"
        )

    @abc.abstractmethod
    def extract_content(self, url: Url) -> Generator[Content, None, None]:
        """Extract content from the given URL.

        Args:
            url (~megu.models.content.Url):
                The URL to extract content from.

        Yields:
            :class:`~megu.models.content.Content`:
                The discovered content from the given URL.
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__!s} must implement extract_content method"
        )

    @abc.abstractmethod
    def merge_manifest(self, manifest: Manifest, to_path: Path) -> Path:
        """Merge downloaded artifacts from a manifest to a singular local filepath.

        Args:
            manifest (~megu.models.content.Manifest):
                The manifest containing the content and its downloaded artifacts.
            to_path (~pathlib.Path):
                The path to merge to artifacts to.

        Returns:
            ~pathlib.Path:
                The path the artifacts have been merged to.
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__!s} must implement merge_manifest method"
        )
