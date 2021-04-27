# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains the plugin group of commands."""

import typer

from ..constants import PLUGIN_DIR
from ..log import instance as log
from ..plugin.discover import discover_plugins, iter_available_plugins
from ..plugin.manage import add_plugin, remove_plugin
from .style import Colors, Symbols
from .ui import build_spinner, display_plugin
from .utils import get_echo, is_debug_context

plugin_app = typer.Typer(help="Control available plugins.")


@plugin_app.command("add")
@log.catch()
def plugin_add(ctx: typer.Context, plugin: str):
    """Install a plugin via pip."""

    echo = get_echo(ctx)
    with build_spinner(
        ctx,
        text=f"Add Plugin {Colors.success | plugin} {Symbols.right_arrow} ",
        side="right",
        reraise=False,
        report=False,
    ) as spinner:
        package_dirpath = add_plugin(
            plugin, silence_subprocess=(not is_debug_context(ctx))
        )
        spinner.ok(Colors.success | Symbols.success)
        echo("\n")
        for package_name, plugins in discover_plugins(package_dirpath):
            display_plugin(ctx, package_name, plugins)


@plugin_app.command("remove")
@log.catch()
def plugin_remove(ctx: typer.Context, plugin: str):
    """Remove an installed plugin."""

    with build_spinner(
        ctx,
        text=f"Remove Plugin {Colors.success | plugin} {Symbols.right_arrow} ",
        side="right",
        reraise=False,
    ):
        remove_plugin(plugin)


@plugin_app.command("list")
@log.catch()
def plugin_list(ctx: typer.Context):
    """List available plugins."""

    echo = get_echo(ctx, nl=True)
    echo(f"List Plugins {Colors.debug | PLUGIN_DIR.as_posix()}\n")

    plugin_count = 0
    for package_name, plugins in iter_available_plugins(PLUGIN_DIR):
        plugin_count += 1
        display_plugin(ctx, package_name, plugins)
    else:
        if plugin_count <= 0:
            echo(Colors.error | "No available plugins")
