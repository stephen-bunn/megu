# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logic for handling HTTP downloads."""

import warnings
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

from cached_property import cached_property
from requests import Session

from ..constants import STAGING_DIRPATH
from ..log import instance as log
from ..models import Content, HttpResource
from ..models.content import Resource
from .base import BaseDownloader

DEFAULT_CHUNK_SIZE = 2 ** 12
DEFAULT_MAX_CONNECTIONS = 8


class HttpDownloader(BaseDownloader):
    """Downloader for traditional HTTP resources."""

    @cached_property
    def session(self) -> Session:
        """HTTP session to use for downloading resources.

        Returns:
            :class:`~requests.Session`:
                The HTTP session to use for downloading resources.
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

        return all(isinstance(resource, HttpResource) for resource in content.resources)

    def download_resource(
        self,
        resource: HttpResource,
        resource_index: int,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> Tuple[int, Resource, Path]:
        """Download some resource to a specific filepath.

        Args:
            request (~types.HTTPResource):
                The resource to download.
            to_path (:class:`pathlib.Path`):
                The filepath to download the resource to.
            chunk_size (int, optional):
                The byte size of chunks to stream the resource data in.
                Defaults to DEFAULT_CHUNK_SIZE.

        Returns:
            :class:`pathlib.Path`:
                The path the resource was downloaded to.
        """

        with log.contextualize(resource=resource):
            log.debug(f"Making request for resource {resource.fingerprint!r}")
            response = self.session.send(resource.to_request(), stream=True)
            log.success(
                f"Resource {resource.fingerprint!r} resolved to status "
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

        return (resource_index, resource, to_path)

    def _get_content_size(self, content: Content) -> int:
        """Get the full byte size of the given content.

        Args:
            content (~.types.Content):
                The content to get the byte size of.

        Returns:
            int:
                The size of the given content.
        """

        size = 0

        for resource in content.resources:
            if not isinstance(resource, HttpResource):
                warnings.warn(
                    f"{self.__class__.__qualname__!s} encountered resource "
                    f"{resource!r}, expected instance of {HttpResource!r}"
                )
                continue

            response = self.session.head(resource.url)
            size += int(response.headers.get("Content-Length", 0))

        return size

    def download_content(
        self,
        content: Content,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
    ) -> List[Tuple[Resource, Path]]:
        """Download the resource of some content to temporary storage.

        Args:
            content (~.types.Content):
                The content to download.
            max_connections (int, optional):
                The limit of connections to make to handle downloading the content.
                Defaults to DEFAULT_MAX_CONNECTIONS.

        Yields:
            Tuple[~models.content.Resource, Path]:
                A tuple of the resource and the path the resource was downloaded to.
        """

        results: List[Tuple[int, Resource, Path]] = []
        request_futures: Dict[Future, Resource] = {}
        with ThreadPoolExecutor(max_workers=max_connections) as executor:
            for resource_index, resource in enumerate(content.resources):
                to_path = STAGING_DIRPATH.joinpath(
                    f"{content.id!s}.{resource.fingerprint!s}"
                )
                request_futures[
                    executor.submit(
                        self.download_resource,
                        *(resource, resource_index, to_path),
                    )
                ] = resource

            for future in as_completed(request_futures):
                results.append(future.result())

        return [
            (resource, resource_path)
            for _, resource, resource_path in sorted(
                results, key=lambda result: result[0]
            )
        ]
