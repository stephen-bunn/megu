from typing import Callable, Generator, Iterable
from pathlib import Path
from shutil import copy2

from megu.types import UpdateHook
from megu.plugin.base import BasePlugin
from megu.models import URL, Content, ContentManifest
from megu.download.base import BaseDownloader
from megu.download import iter_downloaders
from megu.plugin import iter_plugins
from megu.plugin.generic import GenericPlugin
from megu.helpers import temporary_file
from megu.filters import best_content


def normalize_url(url: str | URL) -> URL:
    return url if isinstance(url, URL) else URL(url)


def get_plugin(url: URL, plugin_dirpath: Path | None = None) -> BasePlugin:
    for _, plugins in iter_plugins(plugin_dirpath=plugin_dirpath):
        for plugin in plugins:
            if url.netloc.decode("utf-8") not in plugin.domains:
                continue

            if not plugin.can_handle(url):
                continue

            return plugin

    return GenericPlugin()


def iter_content(plugin: BasePlugin, url: str | URL) -> Generator[Content, None, None]:
    yield from plugin.iter_content((url if isinstance(url, URL) else URL(url)))


def write_content(plugin: BasePlugin, manifest: ContentManifest, to_path: Path) -> Path:
    if to_path.exists():
        raise FileExistsError(f"File at {to_path} already exists")

    content_id, _ = manifest
    with temporary_file(content_id, "wb") as (temp_filepath, _):
        copy2(plugin.write_content(manifest, temp_filepath), to_path)
        return to_path


def get_downloader(content: Content) -> BaseDownloader:
    for downloader in iter_downloaders():
        if not downloader.can_handle(content):
            continue

        return downloader()

    raise ValueError(f"Failed to find a downloader that can handle content {content}")


def download(
    url: str | URL,
    to_path: Path,
    overwrite: bool = False,
    content_filter: Callable[[Iterable[Content]], Iterable[Content]] | None = None,
    plugin_dirpath: Path | None = None,
    update_hook: UpdateHook | None = None,
) -> Generator[Path, None, None]:
    if not overwrite and to_path.is_file():
        raise FileExistsError(f"File at {to_path} already exists")

    url = normalize_url(url)
    plugin = get_plugin(url, plugin_dirpath=plugin_dirpath)
    sieve = content_filter if content_filter is not None else best_content
    for content in sieve(plugin.iter_content(url)):
        try:
            downloader = get_downloader(content)
        except Exception:
            continue

        yield plugin.write_content(
            downloader.download_content(content, update_hook=update_hook),
            to_path,
        )
