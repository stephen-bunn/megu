# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""The main module for the CLI app."""

from pathlib import Path

import typer
from chalky import configure as configure_chalky
from chalky.shortcuts import sty
from tqdm import tqdm

from ..filters import best_content
from ..hasher import HashType, hash_file
from ..log import configure_logger, get_logger
from ..plugin.generic import GenericPlugin
from ..services import get_downloader, get_plugin, merge_manifest, normalize_url
from .plugin import plugin_app
from .style import Colors, Symbols
from .utils import get_echo, is_debug_context, setup_app

LOG_VERBOSITY_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
DEFAULT_DOWNLOAD_DIRPATH = Path.home().joinpath("Downloads")

app = typer.Typer()
app.add_typer(plugin_app, name="plugin")


@app.callback()
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
def get(
    ctx: typer.Context,
    from_url: str = typer.Argument(..., metavar="URL"),
    to_dir: str = typer.Option(
        DEFAULT_DOWNLOAD_DIRPATH.as_posix(),
        "--dir",
        "-d",
        help="The directory to save to.",
    ),
):
    """Download content from a given url."""

    url = normalize_url(from_url)

    echo = get_echo(ctx)
    echo(f"{sty.bold | 'Get'} {Colors.info | url.url}\n")

    # discover the appropriate plugin for the URL
    plugin = get_plugin(url)
    plugin_color = (
        Colors.warning if isinstance(plugin, GenericPlugin) else Colors.success
    )
    echo(
        f"Using plugin {plugin_color | plugin.name} "
        f"{Colors.debug | plugin.domains}\n\n"
    )

    # discover the appropriate content to download
    for content in best_content(plugin.extract_content(url)):
        with tqdm(
            total=content.size,
            desc=f"  {Colors.info | content.filename}  {Symbols.right_arrow}",
            bar_format="{desc}  {percentage:0.1f}%",
            disable=is_debug_context(ctx),
        ) as progress:

            # verify content file doesn't already exist
            to_path = Path(to_dir, content.filename).expanduser().absolute()
            if to_path.exists():
                # if no checksums are defined, let's assume the file is valid
                if len(content.checksums) <= 0:
                    progress.bar_format = "{desc}  " + (
                        Colors.error | f"{to_path.as_posix()} exists"
                    )
                    continue

                # if checksums are defined, validate the file against one of them
                first_checksum = content.checksums[0]
                hash_type = HashType(first_checksum.type)
                if hash_file(to_path, {hash_type})[hash_type] == first_checksum.hash:
                    progress.bar_format = "{desc}  " + (
                        Colors.error | f"{to_path.as_posix()} exists"
                    )
                    continue

            # get the appropriate downloader
            downloader = get_downloader(content)
            manifest = downloader.download_content(content, update_hook=progress.update)
            final_path = merge_manifest(plugin, manifest, to_path)
            progress.bar_format = f"{{desc}}  {Colors.success | final_path.as_posix()}"
