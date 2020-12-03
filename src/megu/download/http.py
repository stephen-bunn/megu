# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logic for handling HTTP downloads."""

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from functools import cached_property
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Optional, Tuple

from requests.sessions import PreparedRequest, Session

from ..constants import STAGING_DIRPATH
from ..log import instance as log
from ..types import Content
from .base import BaseDownloader

DEFAULT_CHUNK_SIZE = 2 ** 12
DEFAULT_MAX_CONNECTIONS = 8


class HttpDownloader(BaseDownloader):
    """Downloader for traditional HTTP artifacts."""

    @cached_property
    def session(self) -> Session:
        """HTTP session to use for downloading artifacts.

        Returns:
            :class:`~requests.Session`:
                The HTTP session to use for downloading artifacts.
        """

        if not hasattr(self, "_session"):
            self._session = Session()
        return self._session

    @classmethod
    def can_handle(cls, content: Content) -> bool:
        """Check if some given content can be handled by the HTTP downloader.

        Args:
            content (:class:`~.types.Content`):
                The content to check against the current content.

        Returns:
            bool: True if the downloader can handle downloading the content,
                otherwise False
        """

        # FIXME: really stupid implementation for WIP testing
        return True

    def download_request(
        self,
        request: PreparedRequest,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        progress_hook: Optional[Callable[[PreparedRequest, int, int], Any]] = None,
    ) -> Path:
        """Download some artifact to a specific filepath.

        Args:
            request (:class:`requests.PreparedRequest`):
                The artifact to download.
            to_path (:class:`pathlib.Path`):
                The filepath to download the artifact to.
            chunk_size (int, optional):
                The byte size of chunks to stream the artifact data in.
                Defaults to DEFAULT_CHUNK_SIZE.
            progress_hook (Callable[[PreparedRequest, int, int], Any], optional):
                Progress callable to record an artifacts download preogress.
                Defaults to None.

        Returns:
            :class:`pathlib.Path`:
                The path the artifact was downloaded to.
        """

        log.debug(f"Making request {request!r}")
        response = self.session.send(request, stream=True)
        log.success(f"Request {request!r} resolved to {response!r}")

        total_size = int(response.headers["Content-Length"])
        self.allocate_storage(to_path, total_size)
        if progress_hook:
            progress_hook(request, 0, total_size)

        current_size = 0

        with to_path.open("wb") as file_handle:
            log.info(
                f"Downloading content of length {total_size!s} from {response!r} in "
                f"chunks of {chunk_size!s} bytes"
            )
            for chunk in response.iter_content(chunk_size=chunk_size):
                file_handle.write(chunk)
                current_size += len(chunk)

                if progress_hook:
                    progress_hook(request, current_size, total_size)

        return to_path

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

        request_futures: Dict[Future, PreparedRequest] = {}
        with ThreadPoolExecutor(max_workers=max_connections) as executor:
            for request_index, request in enumerate(content.requests):
                to_path = STAGING_DIRPATH.joinpath(f"{content.id!s}.{request_index!s}")
                request_futures[
                    executor.submit(self.download_request, *(request, to_path))
                ] = request

            for future in as_completed(request_futures):
                yield (request_futures[future], future.result())
