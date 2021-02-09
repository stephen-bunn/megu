# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains generic helpers that the CLI needs to isolate."""

from contextlib import contextmanager
from functools import lru_cache
from typing import Dict, Generator, List, Optional

import typer
from yaspin import yaspin
from yaspin.core import Yaspin

from ..constants import CONFIG_DIRPATH, LOG_DIRPATH, PLUGIN_DIRPATH
from ..helpers import noop
from ..log import instance as log
from ..plugin.base import BasePlugin
from ..plugin.discover import discover_plugins
from .style import Colors, Symbols


def setup_app():
    """Handle setting up the application environment on the local machine."""

    for required_dirpath in (
        CONFIG_DIRPATH,
        PLUGIN_DIRPATH,
        LOG_DIRPATH,
    ):
        if not required_dirpath.is_dir():
            log.info(f"Creating required directory at {required_dirpath!s}")
            required_dirpath.mkdir(mode=0o777)


def is_debug_context(ctx: typer.Context) -> bool:
    """Determine if the current context is marked for extra debugging.

    This function may not work for commands grouped under a different Typer instance.
    I haven't yet run into the need for that functionality. But if I do, I will need to
    find a better solution than this fairly naive check.

    Args:
        ctx (typer.Context):
            The current commands context instance.

    Returns:
        bool:
            True if the parent context is marked for debug output, otherwise False.
    """

    return ctx.parent is not None and (
        ctx.parent.params.get("debug", False) or ctx.parent.params.get("verbose", 0) > 0
    )


def noop_spinner(spinner: Yaspin):
    """Effectively noop a spinner in-place.

    Args:
        spinner (~yaspin.core.Yaspin):
            The spinner to noop.
    """

    spinner.stop()
    spinner.stop = noop
    spinner.write = noop
    spinner.start = noop
    spinner.ok = noop
    spinner.fail = noop


@contextmanager
def build_spinner(
    *args,
    report: bool = True,
    reraise: bool = True,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    **kwargs,
) -> Generator[Yaspin, None, None]:
    """Context manager for creating a basic spinner using yaspin.

    Args:
        report (bool):
            If truthy, will report success status.
            Defaults to True.
        reraise (bool):
            If truthy will reraise caught exceptions.
            Defaults to True.
        success_msg (Optional[str]):
            A custom message for when the spinner exits cleanly.
            Defaults to None.
        error_msg (Optional[str]):
            A custom message for when the spinner exists with an exception.
            Defaults to None.

    Yields:
        ~yaspin.core.Yaspin:
            The constructed yaspin spinner instance.
    """

    spinner = yaspin(*args, **kwargs)
    try:
        spinner.start()
        yield spinner
        if report:
            if success_msg is None:
                success_msg = Symbols.success
            spinner.ok(Colors.success | success_msg)
    except Exception as exc:
        if error_msg is None:
            error_msg = f"{Symbols.error!s} {exc!s}"
        spinner.fail(Colors.error | error_msg)
        if reraise:
            raise exc
    finally:
        spinner.stop()


@lru_cache
def get_plugins() -> Dict[str, List[BasePlugin]]:
    """Get the default dictionary of plugins available.

    Returns:
        Dict[str, List[:class:`~.plugin.base.BasePlugin`]]:
            The dictionary of available plugins.
    """

    return dict(discover_plugins(PLUGIN_DIRPATH))
