# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logic for handling HTTP downloads.

Attributes:
    DEFAULT_CHUNK_SIZE (int):
        The default bytesize that the HTTP downloader should use for streaming content.
    DEFAULT_MAX_CONNECTIONS (int):
        The default maximum number of HTTP connections the downloader should use.
    CONTENT_RANGE_PATTERN (~typing.Pattern):
        A compiled regex pattern to help matching content range header values.
"""

import re
import warnings
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from cached_property import cached_property
from requests import Response, Session

from ..constants import STAGING_DIR
from ..log import instance as log
from ..models import Content, HttpResource
from ..models.content import Manifest, Resource
from ..utils import allocate_storage
from .base import BaseDownloader

DEFAULT_CHUNK_SIZE: int = 2 ** 12
DEFAULT_MAX_CONNECTIONS: int = 8

CONTENT_RANGE_PATTERN = re.compile(
    r"^(?P<unit>.*)\s+(?:(?:(?P<start>\d+)-(?P<end>\d+))|\*)\/(?P<size>\d+|\*)$"
)


class HttpDownloader(BaseDownloader):
    """Downloader for traditional HTTP resources."""

    name = "HTTP Downloader"

    @cached_property
    def session(self) -> Session:
        """HTTP session to use for downloading resources.

        Returns:
            ~requests.Session:
                The HTTP session to use for downloading resources.
        """

        if not hasattr(self, "_session"):  # pragma: no cover
            self._session = Session()
        return self._session

    @classmethod
    def can_handle(cls, content: Content) -> bool:
        """Check if some given content can be handled by the HTTP downloader.

        Args:
            content (~models.content.Content):
                The content to check against the current content.

        Returns:
            bool:
                True if the downloader can handle downloading the content,
                otherwise False
        """

        return all(isinstance(resource, HttpResource) for resource in content.resources)

    def _request_resource(
        self, resource: HttpResource, stream: bool = True
    ) -> Response:
        """Request a response for a given HTTP resource.

        Args:
            resource (~models.http.HttpResource):
                The HTTP resource to request.
            stream (bool, optional):
                If True, will open a response stream rather than attempting to fetch
                the full content.
                Defaults to True.

        Returns:
            ~requests.Response:
                The response for the given resource.
        """

        log.info(f"Sending request for resource {resource}")
        return self.session.send(resource.to_request(), stream=stream)

    def _download_normal(
        self,
        resource: HttpResource,
        response: Response,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        update_hook: Optional[Callable[[int], Any]] = None,
    ) -> Path:
        """Handle downloading a normal response for a given HTTP resource.

        Args:
            resource (~models.http.HttpResource):
                The resource that resulted in an OK response.
            response (~requests.Response):
                The OK response.
            to_path (~pathlib.Path):
                The path the content of the resource should be downloaded to.
            chunk_size (int, optional):
                The size in bytes to stream chunks of data from the server.
                Defaults to :attr:`~megu.download.http.DEFAULT_CHUNK_SIZE`.
            update_hook (Optional[Callable[[int], Any]], optional):
                A progress update hook to write the downloaded length of content to.
                Defaults to :data:`None`.

        Returns:
            ~pathlib.Path:
                The path the resource was downloaded to (should be ``to_path``)
        """

        if "content-length" in response.headers:
            total_size = int(response.headers["content-length"])
            allocate_storage(to_path, total_size)

        with to_path.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=chunk_size):
                file_handle.write(chunk)

                if update_hook is not None:
                    update_hook(len(chunk))

        return to_path

    def _download_partial(  # noqa: C901
        self,
        resource: HttpResource,
        response: Response,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        update_hook: Optional[Callable[[int], Any]] = None,
    ) -> Path:
        """Handle downloading a partial response for a given HTTP resource.

        Args:
            resource (~models.http.HttpResource):
                The resource that resulted in a partial response.
            response (~requests.Response):
                The partial response.
            to_path (~pathlib.Path):
                The path the content of the resource should be downloaded to.
            chunk_size (int, optional):
                The size in bytes to stream chunks of data from the server.
                Defaults to :attr:`~DEFAULT_CHUNK_SIZE`.
            update_hook (Optional[Callable[[int], Any]], optional):
                A progress update hook to write the downloaded length of content.
                Defaults to :data:`None`.

        Raises:
            ValueError:
                When the downloading of the partial resource fails for any reason.

        Returns:
            ~pathlib.Path:
                The path the resource was downloaded to (should be ``to_path``).
        """

        # in the worst case scenarios where the partial request is not formatted
        # according to the HTTP 206 RFC, we can attempt to fallback to the
        # standard HTTP 200 downloader callable
        fallback_download = partial(
            self._download_normal,
            resource,
            response,
            to_path,
            chunk_size=chunk_size,
            update_hook=update_hook,
        )

        if "content-range" not in response.headers:
            # if we don't have a content-range we are kinda screwed
            # let's just try and handle it with the normal downloader instead
            log.warning(
                "Partial response has no Content-Range header, "
                "falling back to normal HTTP download handler"
            )
            return fallback_download()

        range_match = CONTENT_RANGE_PATTERN.match(
            response.headers["content-range"].strip()
        )
        if not range_match:
            # when we fail to parse content-range as defined by the RFC, might as well
            # fallback to the normal downloader
            log.warning(
                "Partial response has invalid Content-Range header, "
                "falling back to normal HTTP download handler"
            )
            return fallback_download()

        range_groups = range_match.groupdict()
        if "start" not in range_groups or "end" not in range_groups:
            # without start-end range, we can't paginate over the data properly
            # let's see if the normal downloader can deal with it
            log.warning(
                "Partial response has no valid ranges in the Content-Range header, "
                "falling back to normal HTTP download handler"
            )
            return fallback_download()

        range_size = range_groups.get("size")
        total_size = (
            int(range_size)
            if range_size is not None and range_size not in ("", "*")
            else None
        )
        if total_size is not None:
            total_size = int(total_size)
            allocate_storage(to_path, total_size)

        # handle the first response
        with to_path.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=chunk_size):
                file_handle.write(chunk)

                if update_hook is not None:
                    update_hook(len(chunk))

        # handle iteration over paginated resource using Range header
        range_iterator = self._iter_ranges(
            int(range_groups["start"]),
            int(range_groups["end"]),
            size=total_size,
        )
        # skip first iteration of ranges since we already handled the original
        # response from download_resource
        try:
            next(range_iterator)
        except StopIteration:
            if total_size is not None:
                log.warning(
                    f"Encountered failed iteration for given range in {range_groups},"
                    " assuming content was fetched properly"
                )
                return to_path

            raise ValueError(f"Iteration of ranges from {range_groups} failed")

        for start, end in range_iterator:
            range_header = f"{range_groups.get('unit')!s}={start!s}-{end!s}"
            # produce the next resource according to the provided first range
            log.debug(f"Building next resource of {resource} for range {range_header}")
            next_resource = resource.copy()
            next_resource.headers.update({"Range": range_header})

            next_response = self._request_resource(next_resource)
            if not next_response.ok:
                # if we have not defined a total size (meaning the range generator will
                # loop forever), and the response comes back as a failed range spec,
                # it is likely safe to assume the range generator reached the end
                # of the content
                if total_size is None and next_response.status_code in (416,):
                    log.warning(
                        f"Encountered failed response {next_response} but total size "
                        "of content was not specified, assuming content was "
                        "fetched properly"
                    )
                    return to_path

                raise ValueError(
                    f"Response for resource {next_resource} resolved to error "
                    f"status code {next_response.status_code}"
                )

            # we are appending to the pre-existing file
            # make sure to not overwrite the pre-existing content
            with to_path.open("ab") as file_handle:
                for chunk in next_response.iter_content(chunk_size=chunk_size):
                    file_handle.write(chunk)

                    if update_hook is not None:
                        update_hook(len(chunk))

        return to_path

    def download_resource(
        self,
        resource: HttpResource,
        resource_index: int,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        update_hook: Optional[Callable[[int], Any]] = None,
    ) -> Tuple[int, HttpResource, Path]:
        """Download some resource to a specific filepath.

        Args:
            resource (~models.http.HttpResource):
                The resource to download.
            resource_index (int):
                The content's index of the resource in its list of resources.
            to_path (~pathlib.Path):
                The filepath to download the resource to.
            chunk_size (int, optional):
                The byte size of chunks to stream the resource data in.
                Defaults to :attr:`~DEFAULT_CHUNK_SIZE`.
            update_hook (Optional[Callable[[int], Any]], optional):
                Callable for reporting downloaded chunk sizes.
                Defaults to None.

        Raises:
            ValueError:
                When attempting to download the resource fails for any reason.

        Returns:
            Tuple[int, ~models.http.HttpResource, ~pathlib.Path]:
                A tuple containing the index, the resource, and the path the resource
                was downloaded to.
        """

        status_handlers = {200: self._download_normal, 206: self._download_partial}
        with log.contextualize(resource=resource):
            response = self._request_resource(resource)
            log.debug(f"Resource {resource} resolved to status {response.status_code}")

            if not response.ok:
                raise ValueError(
                    f"Response for resource {resource} resolved to error status code "
                    f"{response.status_code}"
                )
            elif response.status_code == 204:
                raise ValueError(f"Response for resource {resource} has no content")
            elif response.status_code in status_handlers:
                download_handler = status_handlers.get(
                    response.status_code,
                    self._download_normal,
                )
                downloaded_path = download_handler(
                    resource,
                    response,
                    to_path,
                    chunk_size=chunk_size,
                    update_hook=update_hook,
                )
                return (resource_index, resource, downloaded_path)
            else:
                raise ValueError(
                    f"Response for resource {resource} resolved to "
                    f"unhandled status code {response.status_code}"
                )

    def _iter_ranges(
        self,
        start: int,
        end: int,
        size: Optional[int] = None,
        chunk_size: Optional[int] = None,
    ) -> Generator[Tuple[int, int], None, None]:
        """Iterate over ranges to make building partial requests easier.

        .. important::
            If no ``size`` argument is provided. This generator will **never** exit
            and it is up to the consumer to forcibly break out of the loop.

        Args:
            start (int):
                The starting range of the request (typically should be set to 0).
            end (int):
                The ending range of the first request.
            size (Optional[int], optional):
                The full size of the data being requested, if available.
                Defaults to :data:`None`.
            chunk_size (Optional[int], optional):
                The custom chunk-size to use for the generated ranges.
                Defaults to :data:`None`.

        Yields:
            Tuple[int, int]:
                The appropriate (start, end) given the conditions.
        """

        def _loop_condition(end: int, size: Optional[int]) -> bool:
            return end <= size if size is not None else True

        while _loop_condition(end, size):
            if start > end:
                break

            yield start, end
            next_end = end + (chunk_size if chunk_size else ((end - start) + 1))
            # cap last range end at full size, if size provided
            if size is not None and next_end > size:
                next_end = size

            start = end + 1
            end = next_end

    def _get_content_size(self, content: Content) -> int:
        """Get the full byte size of the given content.

        Args:
            content (~models.content.Content):
                The content to get the byte size of.

        Returns:
            int:
                The size of the given content.
        """

        size = 0

        for resource in content.resources:
            if not isinstance(resource, HttpResource):  # pragma: no cover
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
        update_hook: Optional[Callable[[int], Any]] = None,
    ) -> Manifest:
        """Download the resource of some content to temporary storage.

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

        results: List[Tuple[int, Resource, Path]] = []
        request_futures: Dict[Future, Resource] = {}
        with ThreadPoolExecutor(max_workers=max_connections) as executor:
            for resource_index, resource in enumerate(content.resources):
                to_path = STAGING_DIR.joinpath(
                    f"{content.id!s}.{resource.fingerprint!s}"
                )
                request_futures[
                    executor.submit(
                        self.download_resource,
                        *(resource, resource_index, to_path),
                        **dict(update_hook=update_hook),
                    )
                ] = resource

            for future in as_completed(request_futures):
                results.append(future.result())

        return Manifest(
            content=content,
            artifacts=[
                (resource, resource_path)
                for _, resource, resource_path in sorted(
                    results, key=lambda result: result[0]
                )
            ],
        )
