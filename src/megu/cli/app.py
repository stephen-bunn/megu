# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""The main module for the CLI app."""

import typer

from ..log import configure_logger, get_logger
from .helpers import setup_app

LOG_VERBOSITY_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

app = typer.Typer()


@app.callback()
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(default=False, help="Enable debug logging."),
    verbosity: int = typer.Option(
        0,
        "--verbose",
        "-v",
        help="Log verbosity level.",
        min=0,
        max=len(LOG_VERBOSITY_LEVELS) - 1,
        count=True,
        clamp=True,
    ),
):
    """Primary pre-callback that gets executed before all commands.

    Args:
        ctx (:class:`typer.Context`):
            The context of the Typer instance.
        debug (bool, optional):
            True if the debugging flag was provided by the user.
            Defaults to typer.Option(default=False, help="Enable debug logging.").
        verbosity (int, optional):
            The level of verbosity to use for logging.
            Defaults to 0.
    """

    logger = get_logger()
    configure_logger(logger, level=LOG_VERBOSITY_LEVELS[verbosity])

    if debug:
        configure_logger(
            logger,
            level=LOG_VERBOSITY_LEVELS[-1],
            debug=True,
            record=True,
        )

    setup_app()
