from abc import ABC, abstractmethod, abstractproperty
from pathlib import Path
from typing import Generator

from megu.models import URL, Content, ContentManifest


class BasePlugin(ABC):
    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}(name={self.name!r}, domains={self.domains!r})"

    @abstractproperty
    def name(self) -> str:
        raise NotImplementedError(f"{self.__class__.__qualname__} must implement name property")

    @abstractproperty
    def domains(self) -> set[str]:
        raise NotImplementedError(f"{self.__class__.__qualname__} must implement domains property")

    @classmethod
    @abstractmethod
    def can_handle(cls, url: URL) -> bool:
        raise NotImplementedError(
            f"{cls.__qualname__} must implement can_handle classmethod method"  # type: ignore
        )

    @abstractmethod
    def iter_content(self, url: URL) -> Generator[Content, None, None]:
        raise NotImplementedError(
            f"{self.__class__.__qualname__} must implement iter_content method"
        )

    @abstractmethod
    def write_content(self, manifest: ContentManifest, to_path: Path) -> Path:
        raise NotImplementedError(
            f"{self.__class__.__qualname__} must implement write_content method"
        )
