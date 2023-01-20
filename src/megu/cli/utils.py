"""This module contains utilities used by the CLI."""

import re
from functools import lru_cache, partial
from typing import Any, TypeVar

from click import Context
from glom import PathAccessError, glom
from glom.core import _MISSING as glom_MISSING
from rich.console import Console
from rich.theme import Theme

from megu.filters import best_content, specific_content
from megu.models import Content, ContentFilter

T = TypeVar("T")


def get_context_param(ctx: Context, key: str, default: T) -> T:
    """Get the value of a parameter from the root context.

    A default MUST be provided, as we cannot verify that the root context will always contain the
    given key.

    Args:
        ctx (Context): The context provided to the command.
        key (str): The key of the parameter from the root context.
        default (T): The default value if the context does not provide a specific parameter.

    Returns:
        T: The value of the key from the root context.
    """

    working_ctx = ctx
    while working_ctx.parent is not None:
        working_ctx = working_ctx.parent

    return working_ctx.params.get(key, default)


@lru_cache(maxsize=1)
def get_console(color: bool | None) -> Console:
    """Get the appropriate rich console to use for printing output.

    Args:
        color (bool | None): False indicates color should be disabled.

    Returns:
        Console: The rich console instance to use for printing output.
    """

    return Console(
        theme=Theme(
            {
                "debug": "dim",
                "info": "cyan",
                "success": "green",
                "warning": "dim yellow",
                "error": "bold red",
                "repr.number": "cyan",
            },
        ),
        no_color=color is False,
    )


def build_content_filter(**conditions) -> ContentFilter:
    """Build a content filter given conditions from the CLI.

    If no conditions are provided, the default content filter is :func:`~megu.filters.best_content`.

    Returns:
        ContentFilter: The content filter to use for filtering content.
    """

    if len(conditions) <= 0:
        return best_content

    filter_conditions = {key: value for key, value in conditions.items() if value is not None}
    if len(filter_conditions) <= 0:
        return best_content

    return partial(specific_content, **filter_conditions)


def build_content_name(content: Content, to_name: str, default: str | None = None) -> str:
    """Build the content name to use for the downloaded content.

    Args:
        content (Content):
            The content being downloaded.
        to_name (str):
            The name format of the content to save the downloaded content to.
        default (str | None, optional):
            The fallback name if the content name could not be built. Defaults to None.

    Raises:
        ValueError: If the content name could not be built and no default is provided.
        ValueError: If building the content name fails.

    Returns:
        str: The built content name to write the content to.
    """

    content_name = to_name
    for match in re.finditer(r"{(\w+(?:\.\w+)?)}", to_name):
        try:
            value = glom(content, match.group(1), default=(default or glom_MISSING))
            if value is None and default is None:
                raise ValueError(
                    f"Building name for content {content.id}, no value found for {match.group(1)!r}"
                )
            elif value is None:
                value = default

        except PathAccessError as exc:
            raise ValueError(f"Building name for content {content.id} failed") from exc

        content_name = re.sub(match.group(0), str(value), content_name)

    return content_name.strip()
