# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logic to discover and load compatible plugins from a directory."""

import importlib
import inspect
import pkgutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Generator, List, Tuple, Type

from ..constants import APP_NAME, PLUGIN_DIRPATH
from ..exceptions import PluginFailure
from ..helpers import python_path
from ..log import instance as log
from .base import BasePlugin


def load_plugin(plugin_name: str, plugin_class: Type[BasePlugin]) -> BasePlugin:
    """Load a plugin instance from a given plugin class.

    Args:
        plugin_name (str):
            The name of the plugin package
        plugin_class (Type[~megu.plugin.base.BasePlugin]):
            The plugin class from the plugin package

    Raises:
        ~megu.exceptions.PluginFailure:
            When the plugin fails to load

    Returns:
        ~megu.plugin.base.BasePlugin:
            The loaded plugin instance
    """

    try:
        plugin = plugin_class()
        log.success(f"Loaded plugin {plugin_class!r} from {plugin_name!r}")
        return plugin
    except Exception as exc:
        plugin_exception = PluginFailure(
            f"Failed to load plugin {plugin_class!r} from {plugin_name!r}, {exc!s}"
        )

        log.exception(plugin_exception)
        raise plugin_exception from exc


def load_plugin_module(module_name: str) -> ModuleType:
    """Load/import a plugin module given the module name.

    Args:
        module_name (str):
            The name of the plugin module

    Raises:
        ~megu.exceptions.PluginFailure:
            When the plugin module fails to import

    Returns:
        ~types.ModuleType:
            The imported plugin module
    """

    try:
        module = importlib.import_module(module_name)
        log.debug(f"Loaded plugin module {module_name!r}")
        return module
    except Exception as exc:
        plugin_exception = PluginFailure(
            f"Failed to import plugin module {module_name!r}, {exc!s}"
        )

        log.exception(plugin_exception)
        raise plugin_exception


def discover_plugins(
    package_dirpath: Path, plugin_type: Type = BasePlugin
) -> Generator[Tuple[str, List[BasePlugin]], None, None]:
    """Discover and load plugins from a given directory of plugin modules.

    Args:
        package_dirpath (~pathlib.Path):
            The path of the directory to look for plugins in.
        plugin_type (~typing.Type, optional):
            The type of plugin to filter for and attempt to load.
            Defaults to :class:`~megu.plugin.BasePlugin`

    Raises:
        ~megu.exceptions.PluginFailure:
            When a discovered plugin fails to load

    Yields:
        Tuple[str, List[:class:`~megu.plugin.BasePlugin`]]:
            A tuple of the plugin name and the instances of exported plugins from that
            plugin module
    """

    package_dirpath = package_dirpath.expanduser().absolute()
    package_dir = package_dirpath.as_posix()
    if not package_dirpath.is_dir():
        log.warning(f"Skipping plugin discovery as {package_dir!r} does not exist")
        return

    with python_path(package_dirpath):
        plugin_prefix = f"{APP_NAME!s}_"

        log.info(f"Discovering plugins in {package_dir!r}")
        for _, plugin_name, _ in pkgutil.iter_modules([package_dir]):
            # filter out modules that are not prefixed with the application name
            if not plugin_name.startswith(plugin_prefix):
                log.warning(
                    f"Module {plugin_name!r} in {package_dir!r} does not use plugin "
                    f"prefix {plugin_prefix!r}, skipping"
                )
                continue

            try:
                log.debug(f"Processing plugin {plugin_name!r}")
                plugin_module = load_plugin_module(plugin_name)
            except PluginFailure:
                continue

            plugins: List[BasePlugin] = []

            for plugin_export in vars(plugin_module).values():
                # filter out exports that are not subclasses of the given plugin_type
                if not (
                    plugin_export is not plugin_type
                    and inspect.isclass(plugin_export)
                    and issubclass(plugin_export, plugin_type)
                ):
                    continue

                try:
                    log.debug(
                        f"Found plugin export {plugin_export!r} in {plugin_name!r}"
                    )
                    plugins.append(load_plugin(plugin_name, plugin_export))
                except PluginFailure:
                    continue

            # skip yielding plugins if no usable plugins are found
            if len(plugins) <= 0:
                continue

            yield (plugin_name, plugins)


def iter_available_plugins(
    plugin_dirpath: Path = PLUGIN_DIRPATH,
    plugin_type: Type = BasePlugin,
) -> Generator[Tuple[str, List[BasePlugin]], None, None]:
    """Get all available plugins from the given plugin directory.

    Args:
        plugin_dirpath (~pathlib.Path, optional):
            The path to the directory where plugins are installed.
            Defaults to :attr:`~megu.constants.PLUGIN_DIRPATH`.
        plugin_type (~typing.Type, optional):
            The type of plugins to load.
            Defaults to :class:`~megu.plugin.BasePlugin`.

    Yields:
        Tuple[str, List[:class:`~megu.plugin.BasePlugin`]]:
            A tuple of the plugin name and the instances of exported plugins from
            available plugin modules.
    """

    for dirpath in filter(lambda d: d.is_dir(), plugin_dirpath.iterdir()):
        yield from discover_plugins(package_dirpath=dirpath, plugin_type=plugin_type)
