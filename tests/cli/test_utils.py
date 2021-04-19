# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains cli utility tests."""

from unittest.mock import patch

from megu.cli.utils import setup_app


def test_setup_app():
    with patch(
        "megu.cli.utils.create_required_directories"
    ) as mock_create_required_directories:
        setup_app()

        mock_create_required_directories.assert_called_once()
