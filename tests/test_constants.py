# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains spot-check tests for constants."""

from pathlib import Path

from megu import constants


def test_APP_NAME_defined():
    assert isinstance(constants.APP_NAME, str)
    assert len(constants.APP_NAME) > 0


def test_APP_VERSION_defined():
    assert isinstance(constants.APP_VERSION, str)
    assert len(constants.APP_VERSION) > 0


def test_CONFIG_DIR_defined():
    assert isinstance(constants.CONFIG_DIR, Path)
