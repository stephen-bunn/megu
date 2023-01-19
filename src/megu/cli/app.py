from itertools import groupby
from pathlib import Path
from typing import Optional

from rich.tree import Tree
from rich.columns import Columns
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.filesize import decimal as format_filesize
from typer import Typer, Context, Option, Argument

from megu import normalize_url, get_plugin, get_downloader, iter_content, write_content
from megu.hash import hash_file, HashType
from megu.config import DOWNLOAD_DIRPATH
from megu.cli.utils import get_console, build_content_filter, build_content_name
from megu.cli.plugin import plugin_app

app = Typer(context_settings={"help_option_names": ["-h", "--help"]})
app.add_typer(plugin_app, name="plugin")


@app.callback()
def main(ctx: Context, color: bool = Option(default=True, help="Enable color output.")):
    ...


@app.command("get")
def get(
    ctx: Context,
    from_url: str = Argument(..., metavar="URL"),
    to_dir: Optional[str] = Option(
        None,
        "--dir",
        "-d",
        help="The directory to save the content to.",
    ),
    to_name: Optional[str] = Option(
        None,
        "--name",
        "-n",
        help="The name format to save content with.",
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

    console = get_console(ctx.color)
    url = normalize_url(from_url)
    plugin = get_plugin(url)

    content_filter = build_content_filter(quality=quality, type=type)
    try:
        download_dirpath = (
            DOWNLOAD_DIRPATH if to_dir is None else Path(to_dir).expanduser().absolute()
        )
        for content in content_filter(iter_content(plugin, url)):
            to_path = download_dirpath.joinpath(
                build_content_name(content, to_name) if to_name is not None else content.filename
            )
            with Progress(
                TextColumn(f"[info]{content.id}[/] [success]{content.name}[/]"),
                BarColumn(),
                TaskProgressColumn(),
                DownloadColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                if not to_path.parent.is_dir():
                    raise ValueError(f"{to_path.parent} does not exist")

                if to_path.exists():
                    if len(content.checksums) <= 0:
                        raise ValueError(f"{to_path} exists")

                    first_checksum = content.checksums[0]
                    hash_type = HashType(first_checksum.type)
                    if hash_file(to_path, {hash_type})[hash_type] == first_checksum.value:
                        raise ValueError(f"{to_path} exists")

                downloader = get_downloader(content)
                download_task = progress.add_task("Downloading", total=content.size)
                manifest = downloader.download_content(
                    content,
                    update_hook=lambda chunk_size, _: progress.advance(download_task, chunk_size),
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

    console = get_console(ctx.color)
    url = normalize_url(from_url)
    url_tree = Tree(f"[debug]{url}[/]")

    plugin = get_plugin(url)

    try:
        for content_id, content in groupby(iter_content(plugin, url), lambda content: content.id):
            content_tree = url_tree.add(f"[info]{content_id}[/]")
            for content_item in sorted(content, key=lambda content: content.quality, reverse=True):
                content_tree.add(
                    Columns(
                        [
                            f"[success]{content_item.name}[/]",
                            f"[debug]({content_item.type})[/]",
                            f"[info]{format_filesize(content_item.size)}[/]",
                        ]
                    )
                )

        console.print(url_tree)
    except Exception:
        console.print_exception()
        raise
