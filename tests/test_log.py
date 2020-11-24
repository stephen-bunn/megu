# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for logging setup."""

from __future__ import annotations

from unittest.mock import patch

import loguru
from hypothesis import given
from hypothesis.strategies import booleans

from megu import constants, log


@given(booleans())
def test_configure_logger(debug: bool):
    with patch.object(
        loguru.logger,
        "configure",
        wraps=loguru.logger.configure,
    ) as mocked_configure, patch.object(
        loguru.logger,
        "bind",
        wraps=loguru.logger.bind,
    ) as mocked_bind:
        logger = log.configure_logger(loguru.logger, debug=debug)
        assert isinstance(logger, loguru.logger.__class__)

        mocked_configure.assert_called_once_with(
            handlers=[log.DEBUG_HANDLER if debug else log.DEFAULT_HANDLER]
        )
        mocked_bind.assert_called_once_with(version=constants.APP_VERSION)


@given(booleans())
def test_get_logger(debug: bool):
    # clear cache since we are LRU caching to avoid unnecessary calls
    log.get_logger.cache_clear()

    with patch.object(
        log,
        "configure_logger",
        wraps=log.configure_logger,
    ) as mock_configure_logger:
        logger = log.get_logger(debug=debug)

        assert isinstance(logger, loguru.logger.__class__)
        mock_configure_logger.assert_called_once_with(loguru.logger, debug=debug)


def test_instance():
    assert isinstance(log.instance, loguru.logger.__class__)
    assert log.get_logger() == log.instance
