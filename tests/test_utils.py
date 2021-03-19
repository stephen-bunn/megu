# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for package utilities."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
from unittest.mock import patch

from hypothesis import given
from hypothesis.strategies import lists

from megu.utils import create_required_directories

from .strategies import pythonic_name


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
