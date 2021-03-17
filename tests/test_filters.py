# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for content filters."""

from typing import List

import pytest
from hypothesis import given
from hypothesis.strategies import just, lists

from megu.filters import best_content
from megu.models import Content

from .strategies import megu_content


@given(
    lists(
        megu_content(id_strategy=just("a")),
        max_size=3,
        min_size=1,
        unique_by=lambda c: c.quality,
    ),
)
def test_best_content_filter(content_list: List[Content]):
    content_iterator = iter(content_list)
    content = next(best_content(content_iterator))
    assert isinstance(content, Content)

    with pytest.raises(StopIteration):
        next(best_content(content_iterator))

    assert max([c.quality for c in content_list]) == content.quality
