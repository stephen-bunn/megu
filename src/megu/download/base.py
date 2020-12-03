# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains the abstractions necessary to build content downloaders."""

import abc
from pathlib import Path
from typing import Any, Callable, Generator, Optional, Tuple

from requests import PreparedRequest

from ..log import instance as log
from ..types import Content

DEFAULT_MAX_CONNECTIONS = 8


class BaseDownloader(abc.ABC):
    """The base downloader that all content downloaders should inherit from."""

    @abc.abstractclassmethod
    def can_handle(cls, content: Content) -> bool:
        """Check if some given content can be handled by the downloader.

        Args:
            content (:class:`~.types.Content`):
                The content to check against the current content.

        Returns:
            bool: True if the downloader can handle downloading the content,
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
        progress_hook: Optional[Callable[[int, int], Any]] = None,
    ) -> Generator[Tuple[PreparedRequest, Path], None, None]:
        """Download the artifacts of some content to temporary storage.

        Args:
            content (:class:`~.types.Content`):
                The content to download.
            max_connections (int, optional):
                The limit of connections to make to handle downloading the content.
                Defaults to DEFAULT_MAX_CONNECTIONS.
            progress_hook (Optional[Callable[[int, int], Any]], optional):
                A callable hook to present the current download status.
                Defaults to None.

        Yields:
            Tuple[PreparedRequest, Path]:
                A tuple of the artifact and the path the artifact was downloaded to.
        """

        raise NotImplementedError(
            f"{self.__class__.__qualname__!s} must implement download_content method"
        )

    def allocate_storage(self, to_path: Path, size: int) -> Path:
        """Allocate a specific number of bytes to a non-existing filepath.

        Args:
            to_path (:class:`pathlib.Path`):
                The filepath to allocate a specific number of bytes to.
            size (int):
                The number of bytes to allocate.

        Raises:
            FileExistsError:
                If the given filepath already exists

        Returns:
            :class:`pathlib.Path`: The given filepath
        """

        if to_path.exists():
            raise FileExistsError(f"Location {to_path!s} already exists")

        if not to_path.parent.is_dir():
            log.debug(f"Creating directory {to_path.parent!s} to allocate {to_path!s}")
            to_path.parent.mkdir(mode=0o777, parents=True)

        log.info(f"Allocating {size!s} bytes at {to_path!s}")
        with to_path.open("wb") as file_handle:
            file_handle.seek(size - 1)
            file_handle.write(b"\x00")

        return to_path
