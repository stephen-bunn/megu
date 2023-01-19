from pkgutil import iter_modules
from importlib import import_module
from pathlib import Path
from typing import Generator, Type

from megu.config import APP_NAME, PLUGIN_DIRPATH
from megu.plugin.base import BasePlugin
from megu.helpers import python_path

PLUGIN_PREFIX = f"{APP_NAME}_"
PLUGINS: dict[str, set[BasePlugin]] = {}


def register_plugin(plugin_class: Type[BasePlugin]):
    plugin_module = plugin_class.__module__.split(".")[0]
    if plugin_module not in PLUGINS:
        PLUGINS[plugin_module] = set()

    PLUGINS[plugin_module].add(plugin_class())


def iter_plugins(
    plugin_dirpath: Path | None = None,
) -> Generator[tuple[str, set[BasePlugin]], None, None]:
    if plugin_dirpath is None:
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
                except Exception:
                    continue

    yield from PLUGINS.items()
