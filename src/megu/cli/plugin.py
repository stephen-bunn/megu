# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains the plugin group of commands."""

from subprocess import CalledProcessError

import typer
from chalky.shortcuts import sty

from ..constants import PLUGIN_DIRPATH
from ..plugin.discover import discover_plugins
from ..plugin.install import install_plugin
from .style import Colors, Symbols
from .utils import get_echo

plugin_app = typer.Typer(help="Control available plugins.")


@plugin_app.command("install")
def plugin_install(ctx: typer.Context, plugin: str):
    """Install a plugin via pip."""

    echo = get_echo(ctx)
    echo(f"{sty.bold | 'Install Plugin'} {Colors.debug | PLUGIN_DIRPATH.as_posix()}\n")

    try:
        echo(f"  {Symbols.right_arrow} {Colors.success | plugin} ... ")
        install_plugin(plugin)
        echo(f"{Colors.success | Symbols.success}\n")
    except CalledProcessError:
        echo(Colors.error | f"Failed to install {plugin}\n")


@plugin_app.command("list")
def plugin_list(ctx: typer.Context):
    """List available plugins."""

    echo = get_echo(ctx, nl=True)
    echo(f"{sty.bold | 'List Plugins'} {Colors.debug | PLUGIN_DIRPATH.as_posix()}")

    plugin_count = 0
    for plugin_name, plugins in discover_plugins(PLUGIN_DIRPATH):
        plugin_count += 1
        echo(f"{Colors.info | plugin_name}")
        for plugin in plugins:
            echo(
                f"  {Symbols.right_arrow} {Colors.success | plugin.name} "
                f"{Colors.debug | plugin.domains}"
            )
    else:
        if plugin_count <= 0:
            echo(Colors.error | "No available plugins")
