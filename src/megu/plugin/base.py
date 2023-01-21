"""This module contains the definition of a BasePlugin that all plugins should inherit."""

from abc import ABC, abstractmethod, abstractproperty
from pathlib import Path
from typing import Generator

from megu.models import URL, Content, ContentManifest


class BasePlugin(ABC):  # pragma: no cover
    """The base plugin interface we rely on."""

    def __str__(self) -> str:
        """Custom string representation of the plugin.

        Returns:
            str: A custom string representation of the plugin instance.
        """

        return f"{self.__class__.__qualname__}(name={self.name!r}, domains={self.domains!r})"

    @abstractproperty
    def name(self) -> str:
        """The name of the plugin.

        This should be a property method, not just a class attribute.
        """

        raise NotImplementedError(f"{self.__class__.__qualname__} must implement name property")

    @abstractproperty
    def domains(self) -> set[str]:
        """The set of handled domains by plugin (compared to url.netloc).

        This should be a property method, not just a class attribute.
        """

        raise NotImplementedError(f"{self.__class__.__qualname__} must implement domains property")

    @classmethod
    @abstractmethod
    def can_handle(cls, url: URL) -> bool:
        """Class method to determine if a given URL can be handled by the plugin.

        Args:
            url (URL): The URL to check if it can be handled by the plugin.

        Returns:
            bool: True if the given URL can be handled by the plugin.
        """

        raise NotImplementedError(
            f"{cls.__qualname__} must implement can_handle classmethod method"
        )

    @abstractmethod
    def iter_content(self, url: URL) -> Generator[Content, None, None]:
        """Discover and iterate over content discovered from the given URL.

        Args:
            url (URL): The URL to use for content discovery.

        Yields:
            Content: Discovered content from the URL.
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__} must implement iter_content method"
        )

    @abstractmethod
    def write_content(self, manifest: ContentManifest, to_path: Path) -> Path:
        """Write downloaded content from a given content manifest to a final filepath.

        Args:
            manifest (ContentManifest): The content manifest containing downloaded artifacts.
            to_path (Path): The filepath to write the content to.

        Returns:
            Path: The filepath the content was written to.
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__} must implement write_content method"
        )
