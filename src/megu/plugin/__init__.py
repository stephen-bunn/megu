"""This module contains helpers for the registering and discovery of available plugins."""

import warnings
from importlib import import_module
from inspect import isclass
from pathlib import Path
from pkgutil import iter_modules
from typing import Generator, Type

from megu.config import PLUGIN_DIRPATH, PLUGIN_PREFIX
from megu.errors import MeguWarning
from megu.helpers import python_path
from megu.plugin.base import BasePlugin

PLUGINS: dict[str, set[Type[BasePlugin]]] = {}


def register_plugin(plugin_class: Type[BasePlugin]):
    """Register a plugin for Megu to use.

    This should be called for all exposed plugins as a result of importing a plugin module.
    Do not register a plugin instance, only the class.

    Args:
        plugin_class (Type[BasePlugin]): The plugin class to register for Megu to use.

    Raises:
        ValueError: If the provided plugin class does not appear to be a class.
    """

    if not isclass(plugin_class):
        raise ValueError(f"Failed to register plugin class {plugin_class}, make sure it is a class")

    plugin_module = plugin_class.__module__.split(".")[0]
    if plugin_module not in PLUGINS:
        PLUGINS[plugin_module] = set()

    PLUGINS[plugin_module].add(plugin_class)


def iter_plugins(
    plugin_dirpath: Path | None = None,
) -> Generator[tuple[str, set[Type[BasePlugin]]], None, None]:
    """Iterate over available registered plugins.

    This does not include the :class:`~megu.plugins.generic.GenericPlugin`.

    Args:
        plugin_dirpath (Path | None, optional):
            The directory to search for plugin modules and plugins. Defaults to None.

    Yields:
        tuple[str, set[Type[BasePlugin]]]:
            A tuple containing the plugin module name along with the set of
            registered plugin instances.
    """

    if plugin_dirpath is None:  # pragma: no cover
        plugin_dirpath = PLUGIN_DIRPATH

    if not plugin_dirpath.is_dir():
        return

    for dirpath in filter(lambda path: path.is_dir(), plugin_dirpath.iterdir()):
        with python_path(dirpath):
            for _, plugin_name, _ in iter_modules([dirpath.as_posix()]):
                if not plugin_name.startswith(PLUGIN_PREFIX):
                    continue

                try:
                    import_module(plugin_name)
                except Exception as error:
                    warnings.warn(
                        f"Failed to import plugins from {dirpath}, {error}",
                        MeguWarning,
                    )
                    continue

    yield from PLUGINS.items()
