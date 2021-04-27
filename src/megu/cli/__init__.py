# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Defines the command line interface namespace."""

from .app import app

__all__ = ["app"]

if __name__ == "__main__":
    app()
