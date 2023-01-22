"""This module contains a simple HTTP downloader for HTTP resources."""

import re
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from copy import copy
from functools import partial
from pathlib import Path
from typing import Generator

from httpx import Client, Response

from megu.config import STAGING_DIRPATH
from megu.download.base import BaseDownloader
from megu.helpers import allocate_storage
from megu.models import Content, ContentManifest, HTTPResource
from megu.types import UpdateHook

DEFAULT_CHUNK_SIZE = 4096
DEFAULT_MAX_CONNECTIONS = 8
CONTENT_RANGE_PATTERN = re.compile(
    r"^(?P<unit>.*)\s+(?:(?:(?P<start>\d+)-(?P<end>\d+))|\*)\/(?P<size>\d+|\*)$"
)


class HTTPDownloader(BaseDownloader):
    """Basic downloader for HTTP resources."""

    @property
    def name(self) -> str:
        """The name of the downloader."""

        return "HTTP Downloader"

    @classmethod
    def can_handle(cls, content: Content) -> bool:  # type: ignore
        """Determine if the downloader can handle the given content.

        This makes sure that all resources are :class:`~megu.models.HttpResource` instances.

        Args:
            content (Content): The content to check if it can be handled by the HTTP Downloader.

        Returns:
            bool: True if the HTTP downloader can handle the provided content.
        """

        return all(isinstance(resource, HTTPResource) for resource in content.resources)

    @property
    def session(self) -> Client:
        """An instance-cahced httpx.Client instance.

        Returns:
            Client: The client to use for fetching resources.
        """

        if not hasattr(self, "_session"):
            self._session = Client()
        return self._session

    def _iter_ranges(
        self,
        start: int,
        end: int,
        total_size: int | None = None,
        chunk_size: int | None = None,
    ) -> Generator[tuple[int, int], None, None]:
        """Iterate over byte ranges for a given start, end, total size, and chunk size.

        Args:
            start (int): The starting bytes.
            end (int): The ending bytes.
            total_size (int | None, optional): The total bytes. Defaults to None.
            chunk_size (int | None, optional): The byte chunk size. Defaults to None.

        Yields:
            tuple[int, int]: A tuple containing the following starting and ending bytes
        """

        if total_size is not None and end >= total_size:
            return

        while end <= total_size if total_size is not None else True:
            if start > end:
                break

            yield start, end

            next_end = end + (chunk_size if chunk_size is not None else (end - start) + 1)
            if total_size is not None and next_end > total_size:
                next_end = total_size

            start = end + 1
            end = next_end

    def _request_resource(self, resource: HTTPResource, stream: bool = True) -> Response:
        """Make a request for the given resource.

        Args:
            resource (HttpResource): The resource to request.
            stream (bool, optional): Whether or not to stream the result. Defaults to True.

        Returns:
            Response: The response of the requested resource.
        """

        return self.session.send(resource, stream=stream)

    def _download_normal(
        self,
        resource: HTTPResource,
        response: Response,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        update_hook: UpdateHook | None = None,
    ) -> Path:
        """Download the HTTP resource assuming it is not a partial resource.

        Args:
            resource (HttpResource):
                The resource to download.
            response (Response):
                The response of the requested resourcce.
            to_path (Path):
                The path to download the resource to.
            chunk_size (int, optional):
                The chunk size to write the content out with. Defaults to DEFAULT_CHUNK_SIZE.
            update_hook (UpdateHook | None, optional):
                The update hook to report on download progress. Defaults to None.

        Returns:
            Path: The filepath the resource was written out to.
        """

        resource_size = None
        # TODO: allocation of storage space _may_ not be necessary
        # does the allocate_storage call even help at all?
        if "Content-Length" in response.headers:  # pragma: no cover
            resource_size = int(response.headers["Content-Length"])
            allocate_storage(to_path, resource_size)

        with to_path.open("wb") as file_io:
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                file_io.write(chunk)

                if update_hook is not None:
                    update_hook(len(chunk), resource_size)

        return to_path

    def _download_partial(  # noqa: C901
        self,
        resource: HTTPResource,
        response: Response,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        update_hook: UpdateHook | None = None,
    ) -> Path:
        """Download the HTTP resource assuming it is a partial resource.

        Args:
            resource (HttpResource):
                The partial resource to download.
            response (Response):
                The response for the partial resource.
            to_path (Path):
                The filepath to write the downloaded resource to.
            chunk_size (int, optional):
                The chunk size to write the content out with. Defaults to DEFAULT_CHUNK_SIZE.
            update_hook (UpdateHook | None, optional):
                The update hook to report on download progress. Defaults to None.

        Raises:
            ValueError: If the iteration of the next partial resource byte ranges fail.
            ValueError: If the request for the next partial resource fails.

        Returns:
            Path: The filepath the content was written out to.
        """

        # in the worst case scenarios where the partial request is not formatted according to the
        # HTTP 206 RFC, we can attempt to fallback to the standard HTTP 200 downloader callable
        fallback_handler = partial(
            self._download_normal,
            resource,
            response,
            to_path,
            chunk_size=chunk_size,
            update_hook=update_hook,
        )

        if "Content-Range" not in response.headers:
            return fallback_handler()

        content_range_match = CONTENT_RANGE_PATTERN.match(response.headers["Content-Range"].strip())
        if content_range_match is None:
            return fallback_handler()

        content_range_groups = content_range_match.groupdict()
        if "start" not in content_range_groups or "end" not in content_range_groups:
            return fallback_handler()

        content_range_size = content_range_groups.get("size")
        resource_size = (
            int(content_range_size)
            if content_range_size is not None and content_range_size not in ("", "*")
            else None
        )
        if resource_size is not None:
            allocate_storage(to_path, resource_size)

        with to_path.open("wb") as file_io:
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                file_io.write(chunk)

                if update_hook is not None:
                    update_hook(len(chunk), resource_size)

        range_iterator = self._iter_ranges(
            int(content_range_groups["start"]),
            int(content_range_groups["end"]),
            resource_size,
        )

        try:
            next(range_iterator)
        except StopIteration:
            if resource_size is not None:
                return to_path

            raise ValueError(f"Iteration of ranges from {content_range_groups} failed")

        for start, end in range_iterator:
            next_resource = copy(resource)
            next_resource.headers.update(
                {"Range": f"{content_range_groups.get('unit')}={start}-{end}"}
            )
            next_response = self._request_resource(next_resource)
            if not next_response.is_success:
                if resource_size is None and next_response.status_code in {416}:
                    return to_path

                raise ValueError(
                    f"Response for resource {next_resource} resolved to error "
                    f"{next_response.status_code}"
                )

            with to_path.open("ab") as file_io:
                for chunk in next_response.iter_bytes(chunk_size=chunk_size):
                    file_io.write(chunk)

                    if update_hook is not None:
                        update_hook(len(chunk), resource_size)

        return to_path

    def _download_resource(
        self,
        resource: HTTPResource,
        resource_index: int,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        update_hook: UpdateHook | None = None,
    ) -> tuple[int, HTTPResource, Path]:
        """Download the given HTTP resource to the provided filepath.

        Args:
            resource (HttpResource):
                The resource to download.
            resource_index (int):
                The index of the resource being downloaded (to preserve ordering).
            to_path (Path):
                The filepath to write the resource data out to.
            chunk_size (int, optional):
                The chunk size to write the content out with. Defaults to DEFAULT_CHUNK_SIZE.
            update_hook (UpdateHook | None, optional):
                The update hook to report on download progress. Defaults to None.

        Raises:
            ValueError: If the request for the resource resolves to a failing status code.
            ValueError: If the request for the resource has no content.
            ValueError: If the request for the resource resolves to an unhandled status code.

        Returns:
            tuple[int, HttpResource, Path]:
                A tuple containing the resource index, the resource, and the path the content was
                downloaded to.
        """

        status_handlers = {200: self._download_normal, 206: self._download_partial}

        response = self._request_resource(resource)
        if not response.is_success:
            raise ValueError(
                f"Response for resource {resource} resolved to error {response.status_code}"
            )
        elif response.status_code == 204:
            raise ValueError(f"Response for resource {resource} has no content")
        elif response.status_code in status_handlers:
            download_handler = status_handlers.get(response.status_code, self._download_normal)

            if to_path.is_file():  # pragma: no cover
                # Removing existing artifact paths, this typically happens when downloads are
                # ungracefully terminated or cancelled through intervention by the user
                to_path.unlink()

            artifact_path = download_handler(
                resource,
                response,
                to_path,
                chunk_size=chunk_size,
                update_hook=update_hook,
            )
            return (resource_index, resource, artifact_path)

        else:
            raise ValueError(
                f"Response for resource {resource} resolved to unhandled status "
                f"{response.status_code}"
            )

    def download_content(
        self,
        content: Content,
        staging_dirpath: Path | None = None,
        update_hook: UpdateHook | None = None,
    ) -> ContentManifest:
        """Download the provided content to the given staging directory.

        Args:
            content (Content):
                The content to download.
            staging_dirpath (Path | None, optional):
                The directory to place downloaded artifacts in. Defaults to None.
            update_hook (UpdateHook | None, optional):
                The update hook to update on progress. Defaults to None.

        Returns:
            ContentManifest: The content manifest containing downloaded artifacts.
        """

        resource_results: list[tuple[int, HTTPResource, Path]] = []
        resource_futures: dict[Future[tuple[int, HTTPResource, Path]], HTTPResource] = {}

        with ThreadPoolExecutor(max_workers=DEFAULT_MAX_CONNECTIONS) as thread_executor:
            for resource_index, resource in enumerate(content.resources):
                to_path = (
                    staging_dirpath if staging_dirpath is not None else STAGING_DIRPATH
                ).joinpath(f"{content.id}.{resource.fingerprint}")
                resource_futures[
                    thread_executor.submit(
                        self._download_resource,
                        resource,
                        resource_index,
                        to_path,
                        update_hook=update_hook,
                    )
                ] = resource

            for future in as_completed(resource_futures):
                resource_results.append(future.result())

        return (
            content.id,
            [
                (resource.fingerprint, artifact_path)
                for _, resource, artifact_path in sorted(
                    resource_results, key=lambda result: result[0]
                )
            ],
        )
