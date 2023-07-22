"""This module contains the base CLI app and commands."""

from itertools import groupby
from pathlib import Path
from typing import List, Optional

from rich.columns import Columns
from rich.filesize import decimal as format_filesize
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.tree import Tree
from typer import Argument, Context, Option, Typer

from megu import get_downloader, get_plugin, iter_content, normalize_url, write_content
from megu.cli.plugin import plugin_app
from megu.cli.utils import build_content_filter, build_content_name, get_console, get_context_param
from megu.config import DOWNLOAD_DIRPATH, PLUGIN_DIRPATH
from megu.hash import HashType, hash_file

app = Typer(context_settings={"help_option_names": ["-h", "--help"]})
app.add_typer(plugin_app, name="plugin")


@app.callback()
def main(
    ctx: Context,
    color: bool = Option(default=True, help="Enable color output."),
    plugin_dir: Path = Option(default=PLUGIN_DIRPATH, help="The directory containing plugins."),
):
    ...


@app.command("get")
def get(
    ctx: Context,
    from_url: List[str] = Argument(..., metavar="URL"),
    to_dir: Optional[str] = Option(
        None,
        "--dir",
        "-d",
        help="The directory to save the content to.",
    ),
    to_output: Optional[str] = Option(
        None,
        "--output",
        "-o",
        help="The name format to save content with.",
    ),
    name: Optional[str] = Option(
        None,
        "--name",
        "-n",
        help="The name of the content to get.",
    ),
    quality: Optional[float] = Option(
        None,
        "--quality",
        "-q",
        help="The quality of content to get.",
    ),
    type: Optional[str] = Option(
        None,
        "--type",
        "-t",
        help="The type of content to get.",
    ),
):
    """Download content from a URL."""

    console = get_console(get_context_param(ctx, "color", True))
    for given_url in from_url:
        url = normalize_url(given_url)
        plugin = get_plugin(
            url,
            plugin_dirpath=get_context_param(ctx, "plugin_dir", PLUGIN_DIRPATH),
        )

        content_filter = build_content_filter(quality=quality, type=type, name=name)
        try:
            download_dirpath = (
                DOWNLOAD_DIRPATH if to_dir is None else Path(to_dir).expanduser().absolute()
            )
            for content in content_filter(iter_content(plugin, url)):
                to_path = download_dirpath.joinpath(
                    build_content_name(content, to_output)
                    if to_output is not None
                    else content.filename
                )

                if not to_path.parent.is_dir():
                    raise ValueError(f"{to_path.parent} does not exist")

                if to_path.exists():
                    if len(content.checksums) <= 0:
                        console.print(f"[warning]{to_path.name} already exists, skipping {url}[/]")
                        continue

                    first_checksum = content.checksums[0]
                    hash_type = HashType(first_checksum.type)
                    if hash_file(to_path, {hash_type})[hash_type] == first_checksum.value:
                        console.print(f"[warning]{to_path.name} already exists, skipping {url}[/]")
                        continue

                with Progress(
                    TextColumn(f"[info]{content.id}[/] [success]{content.name}[/]"),
                    BarColumn(),
                    TaskProgressColumn(),
                    DownloadColumn(),
                    TimeRemainingColumn(),
                    console=console,
                ) as progress:
                    downloader = get_downloader(content)
                    download_task = progress.add_task("Downloading", total=content.size)
                    manifest = downloader.download_content(
                        content,
                        update_hook=lambda content_id, chunk_size, total_size: progress.advance(
                            download_task, chunk_size
                        ),
                    )

                    progress.stop()
                    with console.status(f"[debug]Writing {content.id} to {to_path}[/]"):
                        write_content(plugin, manifest, to_path)
        except Exception:
            console.print_exception()
            raise


@app.command("list")
def list(ctx: Context, from_url: str = Argument(..., metavar="URL")):
    """List content available at a URL."""

    console = get_console(get_context_param(ctx, "color", True))
    url = normalize_url(from_url)
    plugin = get_plugin(url, plugin_dirpath=get_context_param(ctx, "plugin_dir", PLUGIN_DIRPATH))

    try:
        with console.status(f"[debug]Listing {url}...[/]"):
            for content_group, content in groupby(
                iter_content(plugin, url), lambda content: content.group
            ):
                content_tree = Tree(f"[info]{content_group}[/]")
                for content_item in sorted(
                    content, key=lambda content: content.quality, reverse=True
                ):
                    content_tree.add(
                        Columns(
                            [
                                f"[success]{content_item.name}[/]",
                                f"[debug]({content_item.type})[/]",
                                f"[info]{format_filesize(content_item.size)}[/]",
                            ]
                        )
                    )
                console.print(content_tree)
    except Exception:
        console.print_exception()
        raise
