# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains tests for cli styles."""

from inspect import isclass

from megu.cli.style import Colors, Symbols


def test_Colors():
    assert isclass(Colors)


def test_Symbols():
    assert isclass(Symbols)
