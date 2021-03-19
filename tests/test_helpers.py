# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for package helpers."""

import string
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from diskcache import Cache
from hypothesis import given
from hypothesis.strategies import dictionaries, from_regex, lists, sampled_from, text
from requests import Session

from megu.constants import TEMP_DIRPATH
from megu.helpers import (
    DISK_CACHE_PATTERN,
    disk_cache,
    get_soup,
    http_session,
    noop,
    noop_class,
    python_path,
    temporary_directory,
    temporary_file,
)

from .strategies import builtin_types, pathlib_path, pythonic_name


@given(
    lists(builtin_types(), max_size=4),
    dictionaries(keys=pythonic_name(), values=builtin_types(), max_size=4),
    pythonic_name(),
)
def test_noop_class(args: List[Any], kwargs: Dict[str, Any], random_attribute: str):
    instance = noop_class(*args, **kwargs)
    assert isinstance(instance, noop_class)

    assert instance() == instance
    assert getattr(instance, random_attribute) == instance


@given(
    lists(builtin_types(), max_size=4),
    dictionaries(keys=pythonic_name(), values=builtin_types(), max_size=4),
)
def test_noop(args: List[Any], kwargs: Dict[str, Any]):
    assert noop(*args, **kwargs) is None  # type: ignore


def test_http_session():
    with http_session() as session:
        assert isinstance(session, Session)


@given(
    text(string.printable).filter(
        lambda name: DISK_CACHE_PATTERN.match(name) is None,
    )
)
def test_disk_cache_raises_ValueError(cache_name: str):
    with pytest.raises(ValueError):
        with disk_cache(cache_name):
            ...


@given(from_regex(DISK_CACHE_PATTERN, fullmatch=True))
def test_disk_cache(cache_name: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)
        with patch("megu.helpers.CACHE_DIRPATH", temp_dirpath):
            diskcache_dirpath = temp_dirpath.joinpath(cache_name)
            assert diskcache_dirpath.is_dir() == False
            diskcache_dirpath.mkdir(parents=True)

            with disk_cache(cache_name) as cache:
                assert diskcache_dirpath.is_dir() == True
                assert isinstance(cache, Cache)


@given(from_regex(DISK_CACHE_PATTERN, fullmatch=True))
def test_disk_cache_creates_directory(cache_name: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)
        with patch("megu.helpers.CACHE_DIRPATH", temp_dirpath):
            diskcache_dirpath = temp_dirpath.joinpath(cache_name)
            assert diskcache_dirpath.is_dir() == False

            with disk_cache(cache_name) as cache:
                assert diskcache_dirpath.is_dir() == True
                assert isinstance(cache, Cache)


@given(pythonic_name(), sampled_from(["w", "wb"]), pathlib_path())
def test_temporary_file_raises_NotADirectoryError(
    prefix: str, mode: str, dirpath: Path
):
    with pytest.raises(NotADirectoryError):
        with temporary_file(prefix, mode, dirpath):
            ...


@given(pythonic_name(), sampled_from(["w", "wb"]))
def test_temporary_file(prefix: str, mode: str):
    if not TEMP_DIRPATH.is_dir():
        TEMP_DIRPATH.mkdir()

    with temporary_file(prefix, mode) as temp_file:
        (temp_filepath, temp_io) = temp_file
        assert isinstance(temp_filepath, Path)
        assert temp_filepath.is_file() == True
        assert isinstance(temp_io, tempfile._TemporaryFileWrapper)  # type: ignore

    assert temp_filepath.is_file() == False


@given(pythonic_name(), pathlib_path())
def test_temporary_directory_raises_NotADirectoryError(prefix: str, dirpath: Path):
    with pytest.raises(NotADirectoryError):
        with temporary_directory(prefix, dirpath):
            ...


@given(pythonic_name())
def test_temporary_directory(prefix: str):
    if not TEMP_DIRPATH.is_dir():
        TEMP_DIRPATH.mkdir()

    with temporary_directory(prefix) as temp_dirpath:
        assert isinstance(temp_dirpath, Path)
        assert temp_dirpath.is_dir() == True

    assert temp_dirpath.is_dir() == False


def test_python_path_skips_inserts_if_none_provided():
    starting_paths = sys.path.copy()
    with python_path() as paths:
        assert paths == starting_paths


@given(pathlib_path())
def test_python_path_inserts_provided_directories(random_path: Path):
    starting_paths = sys.path.copy()
    with python_path("..", "~", random_path.as_posix()) as paths:
        assert len(paths) - len(starting_paths) == 2


@given(text(string.ascii_letters + string.digits))
def test_get_soup(dom: str):
    soup = get_soup(dom)
    assert isinstance(soup, BeautifulSoup)
