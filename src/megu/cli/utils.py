# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains generic helpers that the CLI needs to isolate."""

from functools import partial
from typing import Any, Callable, Iterable

import typer

from ..filters import best_content, specific_content
from ..helpers import noop
from ..models.content import Content
from ..utils import create_required_directories


def setup_app():
    """Handle setting up the application environment on the local machine."""

    create_required_directories()


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
        nl (bool, optional):
            If True, newlines will be provided at the end of all echos automatically.
            Defaults to False.

    Returns:
        Callable[[str], Any]: The appropriate print callable given the context.
    """

    if is_debug_context(ctx):
        return noop

    return partial(typer.echo, nl=nl)


def get_content_filter(
    ctx: typer.Context, **conditions
) -> Callable[[Iterable[Content]], Iterable[Content]]:
    """Get the appropriate content filter for some given conditions.

    Args:
        ctx (typer.Context):
            The current typer context instance.
        conditions (Dict[str, Any]):
            A set of conditions to match.

    Returns:
        Callable[[Iterable[Content]], Iterable[Content]]:
            A filter callable that yields the content that should be handled.
    """

    if len(conditions) <= 0:
        return best_content

    filter_conditions = {
        key: value for key, value in conditions.items() if value is not None
    }

    if len(filter_conditions) <= 0:
        return best_content

    return partial(specific_content, **filter_conditions)
