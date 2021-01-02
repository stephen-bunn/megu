# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logic for handling HTTP downloads."""

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from cached_property import cached_property
from requests import Session

from ..constants import STAGING_DIRPATH
from ..log import instance as log
from ..types import Artifact, Content
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

    def download_artifact(
        self,
        artifact: Artifact,
        artifact_index: int,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> Tuple[int, Artifact, Path]:
        """Download some artifact to a specific filepath.

        Args:
            request (:class:`requests.PreparedRequest`):
                The artifact to download.
            to_path (:class:`pathlib.Path`):
                The filepath to download the artifact to.
            chunk_size (int, optional):
                The byte size of chunks to stream the artifact data in.
                Defaults to DEFAULT_CHUNK_SIZE.

        Returns:
            :class:`pathlib.Path`:
                The path the artifact was downloaded to.
        """

        with log.contextualize(artifact=artifact):
            log.debug(f"Making request for artifact {artifact.fingerprint!r}")
            response = self.session.send(artifact.to_request(), stream=True)
            log.success(
                f"Artifact {artifact.fingerprint!r} resolved to status "
                f"{response.status_code!r}"
            )

            total_size = int(response.headers["Content-Length"])
            self.allocate_storage(to_path, total_size)

            with to_path.open("wb") as file_handle:
                log.info(
                    f"Downloading content of length {total_size!s} from {response!r} "
                    f"in chunks of {chunk_size!s} bytes"
                )

                for chunk in response.iter_content(chunk_size=chunk_size):
                    file_handle.write(chunk)

        return (artifact_index, artifact, to_path)

    def _get_content_size(self, content: Content) -> int:
        size = 0

        for artifact in content.artifacts:
            response = self.session.head(artifact.url)
            size += int(response.headers.get("Content-Length", 0))

        return size

    def download_content(
        self,
        content: Content,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
    ) -> List[Tuple[Artifact, Path]]:
        """Download the artifacts of some content to temporary storage.

        Args:
            content (:class:`~.types.Content`):
                The content to download.
            max_connections (int, optional):
                The limit of connections to make to handle downloading the content.
                Defaults to DEFAULT_MAX_CONNECTIONS.

        Yields:
            Tuple[PreparedRequest, Path]:
                A tuple of the artifact and the path the artifact was downloaded to.
        """

        results: List[Tuple[int, Artifact, Path]] = []
        request_futures: Dict[Future, Artifact] = {}
        with ThreadPoolExecutor(max_workers=max_connections) as executor:
            for artifact_index, artifact in enumerate(content.artifacts):
                to_path = STAGING_DIRPATH.joinpath(
                    f"{content.id!s}.{artifact.fingerprint!s}"
                )
                request_futures[
                    executor.submit(
                        self.download_artifact,
                        *(artifact, artifact_index, to_path),
                    )
                ] = artifact

            for future in as_completed(request_futures):
                results.append(future.result())

        return [
            (artifact, artifact_path)
            for _, artifact, artifact_path in sorted(
                results, key=lambda result: result[0]
            )
        ]
