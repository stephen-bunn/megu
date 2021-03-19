# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for package services."""

from typing import Union

from hypothesis import given
from hypothesis.provisional import urls
from hypothesis.strategies import one_of

from megu.models.content import Url
from megu.services import normalize_url

from .strategies import megu_url


@given(one_of(urls().filter(lambda u: ":0/" not in u), megu_url()))
def test_normalize_url(url: Union[Url, str]):
    normalized = normalize_url(url)
    assert isinstance(normalized, Url)
