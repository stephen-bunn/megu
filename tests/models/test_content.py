# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains tests for content model classes and types."""

import mimetypes

from hypothesis import given
from hypothesis.strategies import from_regex, none

from megu.models.content import Content

from ..strategies import megu_content


@given(megu_content(extension_strategy=from_regex(r"^\..+$")))
def test_Content_ext_as_provided(content: Content):
    assert content.ext == content.extension


@given(megu_content(extension_strategy=none()))
def test_Content_ext_from_mimetype(content: Content):
    ext = mimetypes.guess_extension(content.type)
    assert content.ext == (ext if ext is not None else "")


@given(megu_content())
def test_Content_filename(content: Content):
    assert content.filename == f"{content.id!s}{content.ext!s}"
