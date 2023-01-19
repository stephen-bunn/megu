from abc import ABC, abstractproperty, abstractclassmethod, abstractmethod
from pathlib import Path

from megu.types import UpdateHook
from megu.models import Content, ContentManifest


class BaseDownloader(ABC):
    @abstractproperty
    def name(self) -> str:
        raise NotImplementedError(f"{self.__class__.__qualname__} must implement name property")

    @abstractclassmethod
    def can_handle(cls, content: Content) -> bool:
        raise NotImplementedError(
            f"{cls.__class__.__qualname__} must implement can_handle classmethod"
        )

    @abstractmethod
    def download_content(
        self,
        content: Content,
        staging_dirpath: Path | None = None,
        update_hook: UpdateHook | None = None,
    ) -> ContentManifest:
        raise NotImplementedError(
            f"{self.__class__.__qualname__} must implement download_content method"
        )
