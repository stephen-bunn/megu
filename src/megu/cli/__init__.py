# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Defines the command line interface namespace."""

from .app import app

__all__ = ["app"]

if __name__ == "__main__":
    app()
