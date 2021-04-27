# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains some style definitions for the CLI interface."""

from chalky.shortcuts import fg, sty


class Colors:
    """Object containing standard colors for the CLI interface."""

    info = fg.blue
    success = fg.green & sty.bold
    error = fg.red & sty.bold
    warning = fg.yellow
    debug = sty.dim


class Symbols:
    """Object containing standard symbols for the CLI interface."""

    success = "✔"
    error = "✗"
    right_arrow = "➜"
