# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains helpful service functions that should really only be used during runtime."""

import shutil
from pathlib import Path
from typing import Generator, Optional, Union

from .config import instance as config
from .download import BaseDownloader, discover_downloaders
from .download.http import HttpDownloader
from .helpers import temporary_file
from .log import instance as log
from .models import Content, Manifest, Url
from .plugin import BasePlugin, iter_available_plugins
from .plugin.generic import GenericPlugin


def normalize_url(url: Union[str, Url]) -> Url:
    """Normalize a given URL to a formatted Url instance.

    Args:
        url (Union[str, ~megu.models.content.Url]):
            The given url as either a string or a Url instance.

    Returns:
        ~megu.models.content.Url:
            The normal Url instance.
    """

    if isinstance(url, Url):
        return url

    log.debug(f"Normalizing url {url!r}")
    return Url(url)


def get_plugin(
    url: Union[str, Url],
    plugin_dirpath: Optional[Path] = None,
) -> BasePlugin:
    """Get the best available plugin for a given url.

    Args:
        url (Union[str, ~megu.models.content.Url]):
            The URL string to fetch the appropriate plugin for.
        plugin_dirpath (Optional[~pathlib.Path]):
            The path to the directory of plugins to read through.
            Defaults to None.

    Returns:
        ~megu.plugin.BasePlugin:
            The best available plugin that can handle the given url.
    """

    url = normalize_url(url)
    dirpath: Path = config.plugin_dir
    if plugin_dirpath is not None and plugin_dirpath.is_dir():
        dirpath = plugin_dirpath.absolute()

    log.debug(
        f"Determining which plugin from {dirpath.as_posix()!r} can handle "
        f"URL {url.url!r}"
    )
    for plugin_name, plugins in iter_available_plugins(plugin_dirpath=dirpath):
        for plugin in plugins:
            with log.contextualize(plugin_name=plugin_name, plugin=plugin):
                if url.netloc not in plugin.domains:
                    log.debug(
                        f"Skipping plugin {plugin!r} from {plugin_name!r}, "
                        f"{url.netloc!r} not in plugin domains {plugin.domains!r}"
                    )
                    continue

                if not plugin.can_handle(url):
                    log.debug(
                        f"Skipping plugin {plugin!r} from {plugin_name!r}, "
                        f"plugin cannot handle url {url!s}"
                    )
                    continue

                log.success(f"Determined plugin {plugin!r} can handle {url.url!r}")
                return plugin

    log.warning(
        f"No plugin found that can handle {url.url!r}, "
        f"falling back to {GenericPlugin!r}"
    )
    return GenericPlugin()


def iter_content(
    url: Union[str, Url],
    plugin: BasePlugin,
) -> Generator[Content, None, None]:
    """Shortcut to discover and iterate over content for a given URL.

    Args:
        url (Union[str, ~megu.models.content.Url]):
            The URL to discover content for.
        plugin (~megu.plugins.BasePlugin):
            The plugin to use for extracting content.

    Yields:
        :class:`~megu.models.content.Content`:
            The content extracted for the URL by the most suitable available plugin.
    """

    url = normalize_url(url)
    log.debug(f"Extracting content from {url} using {plugin}")
    for content in plugin.extract_content(url):
        log.info(f"Extracted content {content} from {url} using {plugin}")
        yield content


def get_downloader(content: Content) -> BaseDownloader:
    """Get the best available downloader for the given content.

    Args:
        content (~megu.models.content.Content):
            The content that the downloader should be able to handle.

    Returns:
        ~megu.download.BaseDownloader:
            The best available downloader instance for the given content.
    """

    for downloader in discover_downloaders():
        if not downloader.can_handle(content):  # type: ignore
            log.debug(
                f"Skipping downloader {downloader!r}, "
                f"downloader cannot handle content {content!r}"
            )
            continue

        log.info(f"Downloader {downloader!r} can handle content {content!r}")
        return downloader()

    log.warning(
        f"No downloader found that can handle content {content!r}, "
        f"falling back to {HttpDownloader!r}"
    )
    return HttpDownloader()


def merge_manifest(plugin: BasePlugin, manifest: Manifest, to_path: Path) -> Path:
    """Merge a manifest with the given plugin and finalize content to the given path.

    Args:
        plugin (~megu.plugin.BasePlugin):
            The plugin that was used to extract the content of the manifest.
        manifest (~megu.models.content.Manifest):
            The resulting content and artifact manifest.
        to_path (~pathlib.Path):
            The path the content should be finalized at.

    Raises:
        FileExistsError:
            If the given output path already exists.

    Returns:
        ~pathlib.Path:
            The path the merged content was finalized to.
    """

    if to_path.exists():
        raise FileExistsError(f"File at {to_path!s} already exists")

    log.info(
        f"Merging downloaded artifacts from {manifest} to {to_path} using {plugin}"
    )
    # manifest artifacts must be merged on the same filesystem, and after,
    # moved to the appropriate output location
    with temporary_file(manifest.content.id, "wb") as (temp_path, _):
        merged_path = plugin.merge_manifest(manifest=manifest, to_path=temp_path)
        shutil.copy2(merged_path, to_path)

        return to_path
