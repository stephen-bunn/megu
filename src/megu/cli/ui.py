# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains utilities specific to the CLI ui and displaying content consistently."""

import sys
from contextlib import contextmanager
from typing import List, Optional

import humanfriendly
import typer
from tqdm import tqdm
from yaspin import yaspin
from yaspin.core import Yaspin

from ..helpers import noop_class
from ..models import Content
from ..plugin import BasePlugin
from .style import Colors, Symbols
from .utils import get_echo, is_debug_context, is_progress_context


@contextmanager
def build_progress(
    ctx: typer.Context,
    *args,
    report: bool = True,
    reraise: bool = True,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None,
    **kwargs,
) -> tqdm:
    """Build a progress bar context manager for the CLI to use.

    Args:
        ctx (~typer.Context):
            The context of the current Typer instance.
        report (bool, optional):
            If True, will report success and failures automatically.
            Defaults to True.
        reraise (bool, optional):
            If True, will reraise any exceptions after failing gracefully.
            Defaults to True.
        success_message (Optional[str], optional):
            The default message when the context is exited successfully.
            Defaults to None.
        error_message (Optional[str], optional):
            The default message when the context is exited from a failure.
            Defaults to None.

    Raises:
        Exception:
            Will reraise any exception if ``reraise`` is set to ``True``.

    Returns:
        ~tqdm.tqdm:
            A tqdm_ progress bar instance.
    """

    # we control if the progress bar is disabled through the context
    kwargs.pop("disable", None)

    with tqdm(
        *args,
        disable=is_debug_context(ctx),
        **kwargs,
    ) as progress:
        try:
            yield progress
            if report:
                if success_message is None:
                    success_message = Symbols.success
                progress.bar_format = f"{{desc}} {Colors.success | success_message}"
        except Exception as exc:
            if report:
                if error_message is None:
                    error_message = f"{Symbols.error!s} {exc!s}"
                progress.bar_format = f"{{desc}} {Colors.error | error_message}"
            if reraise:
                raise exc
        finally:
            progress.close()


@contextmanager
def build_spinner(
    ctx: typer.Context,
    *args,
    report: bool = True,
    reraise: bool = True,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None,
    **kwargs,
) -> Yaspin:
    """Build a spinner context manager for the CLI to use.

    Args:
        ctx (~typer.Context):
            The context of the current Typer instance.
        report (bool, optional):
            If True, will report success and failures automatically.
            Defaults to True.
        reraise (bool, optional):
            If True, will reraise any exceptions after failing gracefully.
            Defaults to True.
        success_message (Optional[str], optional):
            The default message when the context is exited successfully.
            Defaults to None.
        error_message (Optional[str], optional):
            The default message when the context is exited from a failure.
            Defaults to None.

    Raises:
        Exception:
            Will reraise any exception if ``reraise`` is set to ``True``.

    Returns:
        ~yaspin.core.Yaspin:
           A yaspin_ spinner instance.
    """

    if is_debug_context(ctx):
        yield noop_class()
        return

    spinner = yaspin(*args, **kwargs)
    try:
        if is_progress_context(ctx):
            spinner.start()
        else:
            progress_text = kwargs.get("text") or (args[0] if len(args) > 0 else None)
            if progress_text is not None:
                sys.stdout.write(progress_text)
                sys.stdout.flush()

        yield spinner
        if report:
            if success_message is None:
                success_message = Symbols.success

            spinner.ok(Colors.success | success_message)
    except Exception as exc:
        if error_message is None:
            error_message = f"{Symbols.error!s} {exc!s}"

        spinner.fail(Colors.error | error_message)
        if reraise:
            raise exc
    finally:
        spinner.stop()


def format_plugin(plugin: BasePlugin) -> str:
    """Format a given plugin as a user-friendly display string.

    Args:
        plugin (~megu.plugin.base.BasePlugin):
            The plugin to format.

    Returns:
        str:
            The properly formatted string.
    """

    return (Colors.info | plugin.name) + " " + (Colors.debug | plugin.domains)


def display_plugin(ctx: typer.Context, package_name: str, plugins: List[BasePlugin]):
    """Display the results of plugin discovery in a user-friendly way.

    Args:
        ctx (~typer.Context):
            The current context of the active Typer instance.
        package_name (str):
            The name of the package the plugins were loaded from.
        plugins (List[~megu.plugin.base.BasePlugin]):
            The list of loaded plugins from the package.
    """

    if is_debug_context(ctx):
        return

    echo = get_echo(ctx, nl=True)
    echo(f"{Colors.success | package_name}")
    for plugin in plugins:
        echo(f"  {Symbols.right_arrow} {format_plugin(plugin)}")


def format_content(content: Content) -> str:
    """Format the given content as a user-friendly display string.

    Args:
        content (~megu.models.content.Content):
            The content to format.

    Returns:
        str:
            The user-friendly display string for the given content.
    """

    formatted_size = humanfriendly.format_size(content.size)
    return (
        (Colors.info | content.id)
        + (Colors.success | f" {content.quality}")
        + (Colors.debug | f" {content.name} [{content.type}] {formatted_size}")
    )
