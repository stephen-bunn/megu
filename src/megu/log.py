# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logger configuration and creation.

We use `Loguru <https://github.com/Delgan/loguru>`_ to handle all the complexities of
logging.
They work with the concept of a single global logger which is used throughout the entire
application.
Since this project is just a single tool that doesn't need to handle too complex
threading or distributed processing, this style of a single global logger works fine.

Examples:
    Most all usage of this logger should look like the following:

    .. code-block:: python

        from .log import instance as log
        log.debug("My logged message here")


    If you need to re-configure the logger for debug logging or for other intricate
    logging handler settings, you should do so through the
    :func:`~.log.configure_logger` function:

    .. code-block:: python

        from .log import configure_logger, instance
        configure_logger(instance, debug=True)

Attributes:
    instance (:class:`loguru.Logger`):
        The configured global logger instance that should likely always be used.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from typing import Any, Dict

import loguru

from .constants import APP_VERSION

DEFAULT_HANDLER = dict(
    sink=sys.stdout,
    level="CRITICAL",
    format="<level>{level:8s}</level> {message}",
)
DEBUG_HANDLER = dict(
    sink=sys.stdout,
    level="DEBUG",
    format="<dim>{time}</dim> <level>{level:8s}</level> {message}",
    backtrace=True,
    diagnose=True,
)


def configure_logger(logger: loguru.Logger, debug: bool = False) -> loguru.Logger:
    """Configure the global logger.

    Args:
        logger (:class:`loguru.Logger`):
            The global logger instance to configure.
        debug (bool, optional):
            If True, configures the logger with the debug configuration.
            Defaults to False.

    Returns:
        :class:`loguru.Logger`:
            The newly configured global logger
    """

    handler: Dict[str, Any] = (
        DEBUG_HANDLER if debug else DEFAULT_HANDLER  # type: ignore
    )
    logger.configure(handlers=[handler])
    return logger.bind(version=APP_VERSION)


@lru_cache(maxsize=2)
def get_logger(debug=False) -> loguru.Logger:
    """Get the configured global logger.

    Args:
        debug (bool, optional):
            If True, enables debug logging.
            Defaults to False.

    Returns:
        :class:`loguru.Logger`:
            The configured global logger
    """

    return configure_logger(loguru.logger, debug=debug)


instance: loguru.Logger = get_logger()
