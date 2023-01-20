"""This module contains the plugin-specific app and commands."""

import re
import subprocess
import sys
from pathlib import Path
from shutil import copytree, rmtree

from rich.columns import Columns
from rich.tree import Tree
from typer import Context, Typer

from megu import iter_plugins
from megu.cli.utils import get_console, get_context_param
from megu.config import APP_NAME, PLUGIN_DIRPATH
from megu.helpers import temporary_directory

DIST_INFO_PATTERN = re.compile(r"^(?P<package>" + APP_NAME + r"_.*)-.*\.dist-info$")

plugin_app = Typer(help="Control available plugins.")


def _get_package_name(package_dirpath: Path) -> str | None:
    if not package_dirpath.is_dir():
        raise NotADirectoryError(f"No such directory {package_dirpath} exists")

    for path in package_dirpath.iterdir():
        if path.is_file():
            continue

        matches = DIST_INFO_PATTERN.match(path.name)
        if matches is None:
            continue

        package_name = matches.groupdict().get("package", None)
        if not package_name:
            continue

        return package_name

    return None


@plugin_app.command("install")
def plugin_install(ctx: Context, plugin: str):
    """Install a plugin via pip."""

    console = get_console(get_context_param(ctx, "color", True))
    with console.status(f"Install Plugin [info]{plugin}[/info]"), temporary_directory(
        "plugin-install-"
    ) as temp_dirpath:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                plugin,
                "--target",
                temp_dirpath.as_posix(),
                "--progress-bar",
                "off",
                "--no-color",
                "--quiet",
                "--no-input",
                "--exists-action",
                "i",
            ]
        )

        package_name = _get_package_name(temp_dirpath)
        if package_name is None:
            raise ValueError(f"Failed to extract package name from package at {temp_dirpath}")

        package_dirpath = get_context_param(ctx, "plugin_dir", PLUGIN_DIRPATH).joinpath(
            package_name
        )
        if package_dirpath.is_dir():
            raise IsADirectoryError(f"Plugin directory at {package_dirpath} already exists")

        copytree(temp_dirpath, package_dirpath)


@plugin_app.command("uninstall")
def plugin_uninstall(ctx: Context, plugin: str):
    """Uninstall a plugin."""

    console = get_console(get_context_param(ctx, "color", True))
    with console.status(f"Uninstall Plugin [info]{plugin}[/]"):
        package_dirpath = get_context_param(ctx, "plugin_dir", PLUGIN_DIRPATH).joinpath(plugin)
        if not package_dirpath.is_dir():
            console.print(f"No plugin {plugin} exists", style="error")
            return

        rmtree(package_dirpath)


@plugin_app.command("list")
def plugin_list(ctx: Context):
    """List installed plugins."""

    console = get_console(get_context_param(ctx, "color", True))
    plugin_dir = get_context_param(ctx, "plugin_dir", PLUGIN_DIRPATH)
    plugin_tree = Tree(f"[debug]{plugin_dir}[/]")
    for plugin_module, plugins in iter_plugins(plugin_dir):
        module_tree = plugin_tree.add(f"[info]{plugin_module}[/]")
        for plugin in plugins:
            module_tree.add(Columns([f"[success]{plugin.name}[/]", f"[debug]{plugin.domains}[/]"]))

    console.print(plugin_tree)
