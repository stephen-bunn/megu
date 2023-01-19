import re
import sys
from os import PathLike
from contextlib import contextmanager
from typing import Generator, IO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from httpx import Client
from diskcache import Cache

from megu.config import TEMPORARY_DIRPATH, CACHE_DIRPATH

DISK_CACHE_PATTERN = re.compile(r"^[a-z]+[a-z0-9_-]{3,31}[a-z0-9]$")


@contextmanager
def http_session() -> Generator[Client, None, None]:
    client = Client()
    try:
        yield client
    finally:
        client.close()


def allocate_storage(to_path: Path, size: int) -> Path:
    if size <= 0:
        raise ValueError(f"Expected byte size > 0 to allocate, received {size}")

    if to_path.exists():
        raise FileExistsError(f"File at {to_path} already exists")

    if not to_path.parent.is_dir():
        to_path.parent.mkdir(mode=0o777, parents=True)

    with to_path.open("wb") as file_handle:
        file_handle.seek(size - 1)
        file_handle.write(b"\x00")

    return to_path


@contextmanager
def temporary_file(
    prefix: str, mode: str, dirpath: Path | None = None
) -> Generator[tuple[Path, IO], None, None]:
    if dirpath is None:
        dirpath = TEMPORARY_DIRPATH

    if not dirpath.is_dir():
        raise NotADirectoryError(f"No directory at {dirpath} exists")

    with NamedTemporaryFile(prefix=prefix, mode=mode, dir=dirpath) as temp_io:
        yield Path(temp_io.name), temp_io


@contextmanager
def temporary_directory(prefix: str, dirpath: Path | None = None) -> Generator[Path, None, None]:
    if dirpath is None:
        dirpath = TEMPORARY_DIRPATH

    if not dirpath.is_dir():
        raise NotADirectoryError(f"No directory at {dirpath} exists")

    with TemporaryDirectory(prefix=prefix, dir=dirpath) as temp_dir:
        yield Path(temp_dir)


@contextmanager
def python_path(*paths: PathLike) -> Generator[list[str], None, None]:
    original_paths = sys.path.copy()
    try:
        if len(paths) <= 0:
            yield sys.path
        else:
            for directory_name in paths:
                directory_path = Path(directory_name).expanduser().resolve()
                if not directory_path.is_dir():
                    continue

                if directory_path.as_posix() in sys.path:
                    continue

                sys.path.insert(0, directory_path.as_posix())

            yield sys.path

    finally:
        sys.path = original_paths


@contextmanager
def disk_cache(cache_name: str) -> Generator[Cache, None, None]:
    if not DISK_CACHE_PATTERN.match(cache_name):
        raise ValueError(
            f"Disk cache name {cache_name!r} violates the required naming pattern "
            f"{DISK_CACHE_PATTERN.pattern!r}"
        )

    diskcache_dirpath = CACHE_DIRPATH.joinpath(cache_name)
    if not diskcache_dirpath.is_dir():
        diskcache_dirpath.mkdir(mode=0o755, parents=True, exist_ok=True)

    with Cache(diskcache_dirpath.as_posix()) as cache:
        yield cache
