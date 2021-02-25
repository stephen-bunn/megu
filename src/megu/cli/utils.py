# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains generic helpers that the CLI needs to isolate."""

from functools import partial
from typing import Any, Callable

import typer

from ..constants import CONFIG_DIRPATH, LOG_DIRPATH, PLUGIN_DIRPATH, TEMP_DIRPATH
from ..helpers import noop
from ..log import instance as log


def setup_app():
    """Handle setting up the application environment on the local machine."""

    for required_dirpath in (
        CONFIG_DIRPATH,
        PLUGIN_DIRPATH,
        LOG_DIRPATH,
        TEMP_DIRPATH,
    ):
        if not required_dirpath.is_dir():
            log.info(f"Creating required directory at {required_dirpath!s}")
            required_dirpath.mkdir(mode=0o777)


def _get_root_context(ctx: typer.Context) -> typer.Context:
    """Get the very root context instance.

    Args:
        ctx (~typer.Context):
            The provided (potentially nested) context instance.

    Returns:
        ~typer.Context:
            The root context instance.
    """

    if ctx.parent is None:
        return ctx

    context = ctx.parent
    while hasattr(context, "parent") and context.parent is not None:
        context = context.parent

    # this is "technically" a click Context
    return context  # type: ignore


def is_debug_context(ctx: typer.Context) -> bool:
    """Determine if the current context is marked for extra debugging.

    Args:
        ctx (typer.Context):
            The current commands context instance.

    Returns:
        bool:
            True if the context is marked for debug output, otherwise False.
    """

    context = _get_root_context(ctx)
    return context.params.get("debug", False) or context.params.get("verbose", 0) > 0


def is_progress_context(ctx: typer.Context) -> bool:
    """Determine if the current context is marked for progress reporting.

    Args:
        ctx (typer.Context):
            The current commands context instance.

    Returns:
        bool:
            True if the context is marked for progress reporting, otherwise False.
    """

    context = _get_root_context(ctx)
    return context.params.get("progress", True)


def get_echo(ctx: typer.Context, nl: bool = False) -> Callable[[str], Any]:
    """Get the appropriate print callable given the context.

    Args:
        ctx (typer.Context):
            The current typer context instance.

    Returns:
        Callable[[str], Any]: The appropriate print callable given the context.
    """

    if is_debug_context(ctx):
        return noop

    return partial(typer.echo, nl=nl)
