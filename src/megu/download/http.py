import re
from copy import copy
from pathlib import Path
from typing import Generator
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from functools import partial

from httpx import Client, Response

from megu.models import HttpResource
from megu.config import STAGING_DIRPATH
from megu.helpers import allocate_storage
from megu.download.base import BaseDownloader
from megu.types import UpdateHook
from megu.models import Content, ContentManifest

DEFAULT_CHUNK_SIZE = 4096
DEFAULT_MAX_CONNECTIONS = 8

CONTENT_RANGE_PATTERN = re.compile(
    r"^(?P<unit>.*)\s+(?:(?:(?P<start>\d+)-(?P<end>\d+))|\*)\/(?P<size>\d+|\*)$"
)


class HttpDownloader(BaseDownloader):
    @property
    def name(self) -> str:
        return "HTTP Downloader"

    @classmethod
    def can_handle(cls, content: Content) -> bool:  # type: ignore
        return all(isinstance(resource, HttpResource) for resource in content.resources)

    @property
    def session(self) -> Client:
        if not hasattr(self, "_session"):
            self._session = Client()
        return self._session

    def _iter_ranges(
        self,
        start: int,
        end: int,
        size: int | None = None,
        chunk_size: int | None = None,
    ) -> Generator[tuple[int, int], None, None]:
        while end <= size if size is not None else True:
            if start > end:
                break

            yield start, end

            next_end = end + (chunk_size if chunk_size is not None else ((end - start) + 1))
            if size is not None and next_end > size:
                next_end = size

            start = end + 1
            end = next_end

    def _request_resource(self, resource: HttpResource, stream: bool = True) -> Response:
        return self.session.send(resource, stream=stream)

    def _download_normal(
        self,
        resource: HttpResource,
        response: Response,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        update_hook: UpdateHook | None = None,
    ) -> Path:
        resource_size = None
        if "Content-Length" in response.headers:
            resource_size = int(response.headers["Content-Length"])
            allocate_storage(to_path, resource_size)

        with to_path.open("wb") as file_io:
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                file_io.write(chunk)

                if update_hook is not None:
                    update_hook(len(chunk), resource_size)

        return to_path

    def _download_partial(
        self,
        resource: HttpResource,
        response: Response,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        update_hook: UpdateHook | None = None,
    ) -> Path:

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
            size=resource_size,
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
        resource: HttpResource,
        resource_index: int,
        to_path: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        update_hook: UpdateHook | None = None,
    ) -> tuple[int, HttpResource, Path]:
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

            if to_path.is_file():
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
        resource_results: list[tuple[int, HttpResource, Path]] = []
        resource_futures: dict[Future[tuple[int, HttpResource, Path]], HttpResource] = {}

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
