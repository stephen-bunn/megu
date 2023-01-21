"""A plugin-centric HTTP media content extractor and downloader.

This top-level module contains helper functions that are primarily useful for clients using Megu.
"""

from pathlib import Path
from shutil import copy2
from typing import Generator

from megu.download import iter_downloaders
from megu.download.base import BaseDownloader
from megu.filters import best_content
from megu.helpers import temporary_file
from megu.models import URL, Content, ContentFilter, ContentManifest
from megu.plugin import iter_plugins, register_plugin
from megu.plugin.base import BasePlugin
from megu.plugin.generic import GenericPlugin


def normalize_url(url: str | URL) -> URL:
    """Normalize a given URL into the desired URL instance.

    Args:
        url (str | ~megu.models.URL): The URL to normalize.

    Returns:
        ~megu.models.URL: The normalized URL.
    """

    return url if isinstance(url, URL) else URL(url)


def get_plugin(url: URL, plugin_dirpath: Path | None = None) -> BasePlugin:
    """Get the best available plugin instance for the given URL.

    This falls back the to the :class:`~megu.plugins.generic.GenericPlugin` if no plugin was found
    that could handle the provided URL.

    >>> get_plugin(URL("https://www.google.com/"))
    GenericPlugin(name='Generic Plugin', domains={'*'})

    Args:
        url (URL): The URL to find the best plugin to handle.
        plugin_dirpath (Path | None, optional):
            The directory where we should be searching for plugins. Defaults to None.

    Returns:
        BasePlugin: The best plugin instance to handle the URL.
    """

    for _, plugins in iter_plugins(plugin_dirpath=plugin_dirpath):
        for plugin_class in plugins:
            plugin = plugin_class()
            if url.netloc.decode("utf-8") not in plugin.domains:
                continue

            if not plugin.can_handle(url):
                continue

            return plugin

    return GenericPlugin()


def iter_content(plugin: BasePlugin, url: str | URL) -> Generator[Content, None, None]:
    """Iterate over available content using a given plugin for a given URL.

    >>> for content in iter_content(GenericPlugin(), URL("https://www.google.com"/)):
    >>>     print(content)
    Content(...)
    Content(...)

    Args:
        plugin (BasePlugin): The plugin to use for iterating over content.
        url (str | URL): The URL to find and iterate over content.

    Yields:
        Content: Content items discovered from the given plugin.
    """

    yield from plugin.iter_content(normalize_url(url))


def write_content(plugin: BasePlugin, manifest: ContentManifest, to_path: Path) -> Path:
    """Write content from a given manifest out to a given filepath.

    >>> write_content(GenericPlugin(), ContentManifest(...), Path("out.mp4"))
    Path("out.mp4")

    Args:
        plugin (BasePlugin): The plugin to use for writing the content.
        manifest (ContentManifest): The content manifest containing the artifacts from the download.
        to_path (Path): The filepath to write the final content to.

    Raises:
        FileExistsError: If the provided filepath already exists.

    Returns:
        Path: The final content filepath.
    """

    if to_path.exists():
        raise FileExistsError(f"File at {to_path} already exists")

    content_id, _ = manifest
    with temporary_file(content_id, "wb") as (temp_filepath, _):
        copy2(plugin.write_content(manifest, temp_filepath), to_path)
        return to_path


def get_downloader(content: Content) -> BaseDownloader:
    """Get the best available downloader for the given content.

    >>> get_downloader(Content(...))
    HTTPDownloader(...)

    Args:
        content (Content): The content that needs to be downloaded.

    Raises:
        ValueError: If no downloader could be determined as the best for the given content.

    Returns:
        BaseDownloader: The best downloader instance for downloading the given content.
    """

    for downloader in iter_downloaders():
        if not downloader.can_handle(content):
            continue

        return downloader()

    raise ValueError(f"Failed to find a downloader that can handle content {content}")


def download(
    url: str | URL,
    to_dir: Path,
    overwrite: bool = True,
    exists_ok: bool = True,
    content_filter: ContentFilter | None = None,
    plugin_dirpath: Path | None = None,
) -> Generator[Path, None, None]:
    """Shortcut to try and download best content from the given URL using the best plugin.

    By default, this will try and download only the best version of discovered content.
    You can change this by providing a custom `content_filter`.

    Args:
        url (str | URL): The URL to download content from.
        to_dir (Path): The directory to save downloaded content to.
        overwrite (bool, optional): Whether to overwrite existing content. Defaults to True.
        exists_ok: (bool, optional):
            If False will raise a :class:`FileExistsError` if the content already exists at the
            final content path already. Defaults to True.
        content_filter (ContentFilter | None, optional):
            The filter to use for filtering down discovered content. Defaults to None.
        plugin_dirpath (Path | None, optional):
            The directory to use to discover plugins to handle thhe given URL. Defaults to None.

    Raises:
        NotADirectoryError: If the given directory does not exist.
        FileExistsError:
            If the filepath to write content to already exists and we are not overwriting or
            allowing existing files.

    Yields:
        Path: The written filepath of some content extracted from the given URL.
    """

    if not to_dir.is_dir():
        raise NotADirectoryError(f"No directory exists at {to_dir}")

    url = normalize_url(url)
    plugin = get_plugin(url, plugin_dirpath=plugin_dirpath)
    sieve = content_filter if content_filter is not None else best_content
    for content in sieve(plugin.iter_content(url)):
        to_path = to_dir.joinpath(content.filename)
        if to_path.is_file() and not exists_ok and not overwrite:
            raise FileExistsError(f"File exists at {to_path}")

        try:
            downloader = get_downloader(content)
        except Exception:
            continue

        yield plugin.write_content(downloader.download_content(content), to_path)


# Only exposing the helper functions from the top-level module for unspecific imports
__all__ = [
    "register_plugin",
    "normalize_url",
    "get_plugin",
    "iter_content",
    "write_content",
    "get_downloader",
    "download",
]
