# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains some really basic content filters."""

from itertools import groupby
from typing import Iterable

from .models import Content


def best_content(content: Iterable[Content]) -> Iterable[Content]:
    """Get the best quality content from the extracted content iterator.

    Args:
        content (Iterable[~models.Content]):
            The iterable of content that was extracted

    Returns:
        ~models.Content:
            The highest quality content
    """

    for _, content_items in groupby(content, key=lambda c: c.id):
        yield max(content_items, key=lambda c: c.quality)
