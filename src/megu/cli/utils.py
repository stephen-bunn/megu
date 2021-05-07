# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains generic helpers that the CLI needs to isolate."""

import re
from functools import partial
from typing import Any, Callable, Iterable, Optional

import typer
from glom import PathAccessError, glom
from glom.core import _MISSING as glom_MISSING

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


def build_content_filter(
    **conditions,
) -> Callable[[Iterable[Content]], Iterable[Content]]:
    """Get the appropriate content filter for some given conditions.

    Args:
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


def build_content_name(
    content: Content,
    to_name: str,
    default: Optional[str] = None,
) -> str:
    """Build the appropriate content name given a name format string.

    This helper utilizes `glom <https://glom.readthedocs.io/en/latest/index.html>`_
    to access features nested within the content instance to help build a name for the
    content as defined by a given format string.

    This format string should use the traditional string formatting expressions using
    braces "{}". But within these braces, you should be able to supply glom path
    notation syntax using dots to access nested properties.

    Examples:
        >>> build_content_name(content, "{url.domain} - {id}{ext}")
        gfycat.com - gfycat-PepperyVictoriousGalah.mp4

        >>> build_content_name(content, "{meta.title}{ext}")
        Wonder Woman 1984 - I like to party (steps) GIF.mp4

    Args:
        content (~megu.models.Content):
            The content instance that needs a name.
        to_name (str):
            The name format string to use to build a content name.
        default (Optional[str], optional):
            The fallback value for missing format string attributes.
            Defaults to None.

    Raises:
        ValueError:
            When the formatting string contains a non-existent attribute and a default
            fallback value has not been defined.

    Returns:
        str:
            A new fully formatted string using the attributes defined from the given
            formatting string.
    """

    content_name = to_name
    for match in re.finditer(r"{(\w+(?:\.\w+)?)}", to_name):
        try:
            value = glom(content, match.group(1), default=(default or glom_MISSING))
            if value is None and default is not None:
                value = default
            else:
                raise ValueError(
                    f"Building name for content {content.id} failed, "
                    f"value for {match.group(1)!r} resolved to None"
                )
        except PathAccessError as exc:
            # reraise glom's PathAccessError as a standard ValueError so we don't have
            # to capture random library exceptions in the top-level of the CLI.
            raise ValueError(
                f"Building name for content {content.id} failed, {exc.get_message()}"
            )

        content_name = re.sub(match.group(0), str(value), content_name)

    return content_name.strip()
