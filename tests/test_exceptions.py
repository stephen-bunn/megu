# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains spot-check tests for exceptions."""

import string

from hypothesis import given
from hypothesis.strategies import text

from megu.exceptions import MeguException


@given(text(string.printable))
def test_MeguException_contains_message(exception_message: str):
    exception = MeguException(exception_message)
    assert exception.message == exception_message
