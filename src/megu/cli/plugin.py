# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains the plugin group of commands."""

import typer
from chalky.shortcuts import sty

from ..constants import PLUGIN_DIRPATH
from ..plugin.discover import discover_plugins
from .style import Colors, Symbols
from .utils import get_echo

plugin_app = typer.Typer()


@plugin_app.command("list")
def plugin_list(ctx: typer.Context):
    """List available plugins."""

    echo = get_echo(ctx, nl=True)
    echo(f"{sty.bold | 'List Plugins'} {Colors.debug | PLUGIN_DIRPATH.as_posix()}")

    for plugin_name, plugins in discover_plugins(PLUGIN_DIRPATH):
        echo(f"{sty.bold | plugin_name} ({len(plugins)})")
        for plugin in plugins:
            echo(
                f"  {Symbols.right_arrow} {Colors.success | plugin.name} "
                f"{Colors.debug | plugin.domains}"
            )
    else:
        echo(Colors.error | "No available plugins")
