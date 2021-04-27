# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains tests for package utilities."""

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import List
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis.strategies import integers, lists

from megu.utils import allocate_storage, create_required_directories

from .strategies import pathlib_path, pythonic_name


@given(lists(pythonic_name(), min_size=1, max_size=4))
def test_create_required_directories(required_directory_names: List[str]):
    with TemporaryDirectory() as temp_dir:
        temp_dirpath = Path(temp_dir)
        assert temp_dirpath.is_dir() == True

        required_dirpaths = [
            temp_dirpath.joinpath(name) for name in required_directory_names
        ]

        assert all(path.is_dir() == False for path in required_dirpaths)
        with patch("megu.utils.REQUIRED_DIRECTORIES", tuple(required_dirpaths)):
            create_required_directories()
            assert all(path.is_dir() == True for path in required_dirpaths)


@given(pythonic_name(), integers(min_value=1, max_value=1024))
def test_allocate_storage(filename: str, size: int):
    with TemporaryDirectory() as temp_dir:
        to_path = Path(temp_dir).joinpath(filename)
        assert to_path.is_file() == False

        result_path = allocate_storage(to_path, size)
        assert result_path.is_file() == True
        assert result_path.stat().st_size == size


@given(pythonic_name(), pythonic_name(), integers(min_value=1, max_value=1024))
def test_allocate_storage_creates_parents(parent_name: str, filename: str, size: int):
    with TemporaryDirectory() as temp_dir:
        parent_path = Path(temp_dir).joinpath(parent_name)
        assert parent_path.is_dir() == False

        to_path = parent_path.joinpath(filename)
        assert to_path.is_file() == False

        result_path = allocate_storage(to_path, size)
        assert result_path.is_file() == True
        assert result_path.stat().st_size == size


@given(pathlib_path(), integers(max_value=0))
def test_allocate_storage_raises_ValueError(to_path: Path, size: int):
    with pytest.raises(ValueError):
        allocate_storage(to_path, size)


@given(integers(min_value=1, max_value=1024))
def test_allocate_storage_raises_FileExistsError(size: int):
    with NamedTemporaryFile() as temp_file:
        to_path = Path(temp_file.name)
        with pytest.raises(FileExistsError):
            allocate_storage(to_path, size)
