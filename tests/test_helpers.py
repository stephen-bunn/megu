import string
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory, _TemporaryFileWrapper
from unittest.mock import patch

import pytest
from diskcache import Cache
from httpx import Client
from hypothesis import assume, given
from hypothesis.strategies import from_regex, integers, sampled_from, text

from megu.config import TEMPORARY_DIRPATH
from megu.helpers import (
    DISK_CACHE_PATTERN,
    allocate_storage,
    disk_cache,
    http_session,
    python_path,
    temporary_directory,
    temporary_file,
)

from .strategies import DEFAULT_NAME_STRAT, path


def _ensure_temporary_directory():
    if not TEMPORARY_DIRPATH.is_dir():
        TEMPORARY_DIRPATH.mkdir()


def test_http_session():
    with http_session() as session:
        assert isinstance(session, Client)


@given(DEFAULT_NAME_STRAT, integers(min_value=1, max_value=1024))
def test_allocate_storage(filename: str, size: int):
    with TemporaryDirectory() as temp_dir:
        to_path = Path(temp_dir).joinpath(filename)
        assert to_path.exists() == False

        result = allocate_storage(to_path, size)
        assert result.is_file() == True
        assert result.stat().st_size == size


@given(DEFAULT_NAME_STRAT, DEFAULT_NAME_STRAT, integers(min_value=1, max_value=1024))
def test_allocate_storage_creates_parents(parent_name: str, filename: str, size: int):
    with TemporaryDirectory() as temp_dir:
        parent_path = Path(temp_dir).joinpath(parent_name)
        assert parent_path.exists() == False

        to_path = parent_path.joinpath(filename)
        assert to_path.exists() == False

        result = allocate_storage(to_path, size)
        assert result.is_file() == True
        assert result.stat().st_size == size


@given(DEFAULT_NAME_STRAT, integers(max_value=0))
def test_allocate_storage_raises_ValueError_for_invalid_size(to_path: Path, size: int):
    with pytest.raises(ValueError) as error:
        allocate_storage(to_path, size)
        assert f"Expected byte size > 0 to allocate, received {size}" in str(error)


@given(integers(min_value=1, max_value=1024))
def test_allocate_storage_raises_FileExistsError_for_existing_file(size: int):
    with NamedTemporaryFile() as temp_file:
        with pytest.raises(FileExistsError) as error:
            to_path = Path(temp_file.name)
            allocate_storage(to_path, size)
            assert f"File at {to_path} already exists" in str(error)


@given(DEFAULT_NAME_STRAT, sampled_from(["w", "wb"]))
def test_temporary_file(prefix: str, mode: str):
    _ensure_temporary_directory()
    with temporary_file(prefix, mode) as (temp_filepath, temp_io):
        assert isinstance(temp_filepath, Path)
        assert temp_filepath.is_file() == True

        assert isinstance(temp_io, _TemporaryFileWrapper)

    assert temp_filepath.is_file() == False


@given(DEFAULT_NAME_STRAT, sampled_from(["w", "wb"]), path())
def test_temporary_file_raises_NotADirectoryError_for_missing_directory(
    prefix: str, mode: str, dirpath: Path
):
    with pytest.raises(NotADirectoryError):
        with temporary_file(prefix, mode, dirpath):
            ...


@given(DEFAULT_NAME_STRAT)
def test_temporary_directory(prefix: str):
    _ensure_temporary_directory()
    with temporary_directory(prefix) as temp_dirpath:
        assert isinstance(temp_dirpath, Path)
        assert temp_dirpath.is_dir() == True

    assert temp_dirpath.is_dir() == False


@given(DEFAULT_NAME_STRAT, path())
def test_temporary_directory_raises_NotADirectoryError_for_missing_directory(
    prefix: str, dirpath: Path
):
    with pytest.raises(NotADirectoryError):
        with temporary_directory(prefix, dirpath):
            ...


@given(path())
def test_python_path(invalid_path: Path):
    assume(invalid_path.exists() == False)
    original = sys.path.copy()
    # We need to insert existing directories for them to be inserted into the python path
    # Only the `invalid_path` should NOT be inserted into the path
    with python_path(Path(".."), Path("~"), invalid_path):
        assert len(sys.path) - len(original) == 2

    assert sys.path == original


def test_python_path_with_none():
    original = sys.path.copy()
    with python_path():
        assert sys.path == original


def test_python_path_with_existing():
    original = sys.path.copy()
    with python_path(Path(original[0])):
        assert sys.path == original


@given(from_regex(DISK_CACHE_PATTERN, fullmatch=True), sampled_from([True, False]))
def test_disk_cache(cache_name: str, create_dirpath: bool):
    with TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)
        with patch("megu.helpers.CACHE_DIRPATH", temp_dirpath):
            diskcache_dirpath = temp_dirpath.joinpath(cache_name)
            assert diskcache_dirpath.exists() == False
            if create_dirpath:
                diskcache_dirpath.mkdir(mode=0o755, parents=True)

            with disk_cache(cache_name) as cache:
                assert diskcache_dirpath.is_dir() == True
                assert isinstance(cache, Cache)


@given(text(string.printable).filter(lambda name: DISK_CACHE_PATTERN.match(name) is None))
def test_disk_cache_raises_ValueError_for_invalid_name(cache_name: str):
    with pytest.raises(ValueError) as error:
        with disk_cache(cache_name):
            assert f"Disk cache name {cache_name} violates the required naming pattern" in str(
                error
            )
