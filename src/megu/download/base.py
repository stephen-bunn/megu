"""This module contains the definition of a BaseDownloader that all downloaders should inherit."""

from abc import ABC, abstractmethod, abstractproperty
from pathlib import Path

from megu.models import Content, ContentManifest
from megu.types import UpdateHook


class BaseDownloader(ABC):
    """The base downloader interface we rely on."""

    @abstractproperty
    def name(self) -> str:
        """The name of the downloader.

        This should be a property method, not just a class attribute.
        """

        raise NotImplementedError(f"{self.__class__.__qualname__} must implement name property")

    @classmethod
    @abstractmethod
    def can_handle(cls, content: Content) -> bool:
        """Class method to determine if a given content can be handled by the downloader.

        Args:
            content (Content): The content to check if it can be handled by the downloader.

        Returns:
            bool: True if the given content can be handled by the downloader.
        """

        raise NotImplementedError(f"{cls.__qualname__} must implement can_handle classmethod")

    @abstractmethod
    def download_content(
        self,
        content: Content,
        staging_dirpath: Path | None = None,
        update_hook: UpdateHook | None = None,
    ) -> ContentManifest:
        """Download the given content into individual artifacts resulting in a content manifest.

        Args:
            content (Content):
                The content to download.
            staging_dirpath (Path | None, optional):
                The staging directory to store downloaded artifacts. Defaults to None.
            update_hook (UpdateHook | None, optional):
                The update hook to call for download updates. Defaults to None.

        Returns:
            ContentManifest: The resulting content manifest including all content artifacts.
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__} must implement download_content method"
        )
