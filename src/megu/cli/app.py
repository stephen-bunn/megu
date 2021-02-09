# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""The main module for the CLI app."""

import sys
from pathlib import Path

import typer
from chalky.shortcuts import sty

from ..filters import best_content
from ..log import configure_logger, get_logger
from ..plugin.generic import GenericPlugin
from ..services import get_downloader, get_plugin, merge_manifest, normalize_url
from .style import Colors, Symbols
from .utils import build_spinner, is_debug_context, noop_spinner, setup_app

LOG_VERBOSITY_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

app = typer.Typer()


@app.callback()
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(default=False, help="Enable debug logging."),
    verbosity: int = typer.Option(
        0,
        "--verbose",
        "-v",
        help="Log verbosity level.",
        min=0,
        max=len(LOG_VERBOSITY_LEVELS) - 1,
        count=True,
        clamp=True,
    ),
):
    """Megu."""

    logger = get_logger()
    configure_logger(logger, level=LOG_VERBOSITY_LEVELS[verbosity])

    if debug:
        configure_logger(
            logger,
            level=LOG_VERBOSITY_LEVELS[-1],
            debug=True,
            record=True,
        )

    setup_app()


@app.command("get")
def get(ctx: typer.Context, url: str):
    """Get content from a given url."""

    url = normalize_url(url)
    typer.echo((sty.bold | "Get ") + (Colors.info | url) + "\n")

    with build_spinner(
        text=f"  Plugin     {Symbols.right_arrow} ",
        side="right",
        report=False,
        reraise=False,
    ) as spinner:
        if is_debug_context(ctx):
            # if debugging, cancel spinner and noop functionality
            noop_spinner(spinner)

        # discover the appropriate plugin for the URL
        plugin = get_plugin(url)
        plugin_name_color = (
            Colors.warning if isinstance(plugin, GenericPlugin) else Colors.success
        )
        spinner.ok(f"{plugin_name_color | plugin.name} {Colors.debug | plugin.domains}")
        spinner.start()

        # discover the appropriate content to download
        spinner.text = f"  Content    {Symbols.right_arrow} "
        content = best_content(plugin.extract_content(url))
        spinner.ok(Colors.info | content.filename)
        spinner.start()

        # verify content file doesn't already exist
        to_path = Path("~/Downloads", content.filename).expanduser().absolute()
        if to_path.exists():
            spinner.write("")
            spinner.text = (
                Colors.error | f"File at {to_path.as_posix()!s} already exists ..."
            )
            spinner.fail(Colors.error | Symbols.error)
            sys.exit(1)

        # get the appropriate downloader
        spinner.text = f"  Downloader {Symbols.right_arrow} "
        downloader = get_downloader(content)
        spinner.ok(Colors.success | downloader.name)
        spinner.start()

        # download the content and merge the artifacts
        spinner.write("")
        spinner.text = (
            f"Downloading {Colors.info | content.filename} {Symbols.right_arrow} "
        )
        manifest = downloader.download_content(content)
        final_path = merge_manifest(plugin, manifest, to_path)
        spinner.ok(f"{Colors.success | final_path.as_posix()}")
