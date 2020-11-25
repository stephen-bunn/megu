# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains logic to discover and load compatible plugins from a directory."""

import importlib
import inspect
import pkgutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Generator, List, Tuple, Type

from ..constants import APP_NAME
from ..exceptions import PluginFailure
from ..log import instance as log
from .base import BasePlugin


def load_plugin(plugin_name: str, plugin_class: Type[BasePlugin]) -> BasePlugin:
    """Load a plugin instance from a given plugin class.

    Args:
        plugin_name (str):
            The name of the plugin package
        plugin_class (Type[:class:`~.plugin.base.BasePlugin`]):
            The plugin class from the plugin package

    Raises:
        :class:`~.exceptions.PluginFailure`:
            When the plugin fails to load

    Returns:
        :class:`~.plugin.base.BasePlugin`:
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
        :class:`~.exceptions.PluginFailure`:
            When the plugin module fails to import

    Returns:
        :class:`types.ModuleType`:
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
    plugin_dirpath: Path, plugin_type: Type = BasePlugin
) -> Generator[Tuple[str, List[BasePlugin]], None, None]:
    """Discover and load plugins from a given directory of plugin modules.

    Args:
        plugin_dirpath (:class:`pathlib.Path`):
            The path of the directory to look for plugins in
        plugin_type (Type, optional):
            The type of plugin to filter for and attempt to load.
            Defaults to :class:`~.plugin.base.BasePlugin`

    Raises:
        :class:`~.exceptions.PluginFailure`:
            When a discovered plugin fails to load

    Yields:
        Tuple[str, List[:class:`~.plugin.base.BasePlugin`]]:
            A tuple of the plugin name and the instances of exported plugins from that
            plugin module
    """

    plugin_dirpath = plugin_dirpath.expanduser().absolute()
    plugin_dir = plugin_dirpath.as_posix()

    if plugin_dir not in sys.path:
        log.debug(f"Inserting plugin directory {plugin_dir!r} into the Python path")
        sys.path.insert(0, plugin_dir)

    plugin_prefix = f"{APP_NAME!s}_"

    log.info(f"Discovering plugins in {plugin_dir!r}")
    for _, plugin_name, _ in pkgutil.iter_modules([plugin_dir]):
        # filter out modules that are not prefixed with the application name
        if not plugin_name.startswith(plugin_prefix):
            log.warning(
                f"Module {plugin_name!r} in {plugin_dir!r} does not use plugin prefix "
                f"{plugin_prefix!r}, skipping"
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
                log.debug(f"Found plugin export {plugin_export!r} in {plugin_name!r}")
                plugins.append(load_plugin(plugin_name, plugin_export))
            except PluginFailure:
                continue

        # skip yielding plugins if no usable plugins are found
        if len(plugins) <= 0:
            continue

        yield (plugin_name, plugins)
