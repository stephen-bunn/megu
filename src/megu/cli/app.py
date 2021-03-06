# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""The main module for the CLI app."""

from itertools import groupby
from pathlib import Path
from typing import Optional

import typer
from chalky import configure as configure_chalky
from chalky.shortcuts import sty

from ..config import instance as config
from ..hasher import HashType, hash_file
from ..log import configure_logger, get_logger
from ..log import instance as log
from ..services import (
    get_downloader,
    get_plugin,
    iter_content,
    merge_manifest,
    normalize_url,
)
from .plugin import plugin_app
from .style import Colors, Symbols
from .ui import build_progress, format_content, format_plugin
from .utils import build_content_filter, build_content_name, get_echo, setup_app

LOG_VERBOSITY_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})
app.add_typer(plugin_app, name="plugin")


@app.callback()
@log.catch()
def main(
    ctx: typer.Context,
    color: bool = typer.Option(default=True, help="Enable color output."),
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

    configure_chalky(disable=(not color))
    setup_app()


@app.command("get")
@log.catch()
def get(
    ctx: typer.Context,
    from_url: str = typer.Argument(..., metavar="URL"),
    to_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="The directory to save content to.",
    ),
    to_name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="The name format to save content with.",
    ),
    quality: Optional[float] = typer.Option(
        None,
        "--quality",
        "-q",
        help="The exact quality of content to get.",
    ),
    type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="The exact type of content to get.",
    ),
):
    """
    Download all highest quality content provided by the URL.

    $ megu get [URL]

    Download all content provided by the URL to a specific directory.

    $ megu get --dir ~/Desktop [URL]

    Name all downloaded content provided by the URL using a format string.

    $ megu get --name "{url.netloc} - {quality}{ext}" [URL]

    Only download PNG images from the content provided by the URL.

    $ megu get --type image/png [URL]
    """

    url = normalize_url(from_url)

    echo = get_echo(ctx)
    echo(f"{sty.bold | 'Get'} {Colors.info | url.url}\n")

    # discover the appropriate plugin for the URL
    plugin = get_plugin(url)
    echo(f"Using plugin {format_plugin(plugin)}\n\n")

    # discover the appropriate content to download
    content_filter = build_content_filter(quality=quality, type=type)
    try:
        download_dir = (
            config.download_dir
            if to_dir is None
            else Path(to_dir).expanduser().absolute()
        )
        for content in content_filter(iter_content(url, plugin)):
            with build_progress(
                ctx,
                report=False,
                total=content.size,
                desc=f"  {Colors.info | content.id} {Symbols.right_arrow}",
                bar_format="{desc} {percentage:0.1f}%",
            ) as progress:
                # verify content file doesn't already exist
                to_path = download_dir.joinpath(
                    build_content_name(content, to_name)
                    if to_name
                    else content.filename
                )
                if not to_path.parent.is_dir():
                    progress.bar_format = "{desc} " + (
                        Colors.error | f"{to_path.parent} directory does not exist"
                    )
                    continue

                if to_path.exists():
                    # if no checksums are defined, let's assume the file is valid
                    if len(content.checksums) <= 0:
                        progress.bar_format = "{desc} " + (
                            Colors.error | f"{to_path} exists"
                        )
                        continue

                    # if checksums are defined, validate the file against one of them
                    first_checksum = content.checksums[0]
                    hash_type = HashType(first_checksum.type)
                    if (
                        hash_file(to_path, {hash_type})[hash_type]
                        == first_checksum.hash
                    ):
                        progress.bar_format = "{desc} " + (
                            Colors.error | f"{to_path} exists"
                        )
                        continue

                # get the appropriate downloader
                downloader = get_downloader(content)
                manifest = downloader.download_content(
                    content, update_hook=progress.update
                )
                final_path = merge_manifest(plugin, manifest, to_path)
                progress.bar_format = (
                    f"{{desc}} {Colors.success | final_path.as_posix()}"
                )
    except Exception as exc:
        echo(Colors.error | str(exc))
        raise


@app.command("show")
@log.catch()
def show(
    ctx: typer.Context,
    from_url: str = typer.Argument(..., metavar="URL"),
):
    """
    Show all available content from a URL.

    $ megu show [URL]
    """

    url = normalize_url(from_url)

    echo = get_echo(ctx)
    echo(f"{sty.bold | 'Show'} {Colors.info | url.url}\n")

    # discover the appropriate plugin for the URL
    plugin = get_plugin(url)
    echo(f"Using plugin {format_plugin(plugin)}\n\n")

    try:
        for content_id, content in groupby(iter_content(url, plugin), lambda c: c.id):
            echo(f"{Colors.success | content_id}\n")
            for entry in sorted(content, key=lambda c: c.quality, reverse=True):
                echo(f"  {format_content(entry)}\n")

            echo("\n")
    except Exception as exc:
        echo(Colors.error | str(exc))
        raise
