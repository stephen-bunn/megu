# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains utilities specific to the CLI ui and displaying content consistently."""

from contextlib import contextmanager
from typing import List, Optional

import typer
from yaspin import yaspin
from yaspin.core import Yaspin

from megu.plugin.base import BasePlugin

from ..helpers import noop_class
from .style import Colors, Symbols
from .utils import get_echo, is_debug_context


@contextmanager
def build_spinner(
    ctx: typer.Context,
    *args,
    report: bool = True,
    reraise: bool = True,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    **kwargs,
) -> Yaspin:
    """Build a spinner for the CLI to use.

    Args:
        ctx (typer.Context):
            The context of the current Typer instance.
        report (bool, optional):
            If True, will report success and failures automatically.
            Defaults to True.
        reraise (bool, optional):
            If True, will reraise any exceptions after failing gracefully.
            Defaults to True.
        success_msg (Optional[str], optional):
            The default message when the context is exited successfully.
            Defaults to None.
        error_msg (Optional[str], optional):
            The default message when the context is exited from a failure.
            Defaults to None.

    Raises:
        Exception:
            Will reraise any exception if ``reraise`` is set to ``True``.

    Returns:
        ~yaspin.core.Yaspin:
           A :mod:`yaspin` spinner instance.
    """

    if is_debug_context(ctx):
        yield noop_class()
        return

    spinner = yaspin(*args, **kwargs)
    try:
        spinner.start()
        yield spinner
        if report:
            if success_msg is None:
                success_msg = Symbols.success
            spinner.ok(Colors.success | success_msg)
    except Exception as exc:
        if error_msg is None:
            error_msg = f"{Symbols.error!s} {exc!s}"
        spinner.fail(Colors.error | error_msg)
        if reraise:
            raise exc
    finally:
        spinner.stop()


def format_plugin(plugin: BasePlugin) -> str:
    """Format a given plugin as a user-friendly display string.

    Args:
        plugin (~plugin.base.BasePlugin):
            The plugin to format.

    Returns:
        str:
            The properly formatted string.
    """

    return (Colors.info | plugin.name) + " " + (Colors.debug | plugin.domains)


def display_plugin(ctx: typer.Context, package_name: str, plugins: List[BasePlugin]):
    """Display the results of plugin discovery in a user-friendly way.

    Args:
        ctx (typer.Context):
            The current context of the active Typer instance.
        package_name (str):
            The name of the package the plugins were loaded from.
        plugins (List[~plugin.base.BasePlugin]):
            The list of loaded plugins from the package.
    """

    if is_debug_context(ctx):
        return

    echo = get_echo(ctx, nl=True)
    echo(f"{Colors.success | package_name}")
    for plugin in plugins:
        echo(f"  {Symbols.right_arrow}  {format_plugin(plugin)}")
