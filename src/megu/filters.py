"""This module provides basic content filters to wrap :func:`megu.iter_content` or alternatives."""

from functools import reduce
from itertools import groupby
from typing import Generator

from megu.models import Content


def best_content(
    content_iterator: Generator[Content, None, None]
) -> Generator[Content, None, None]:
    """Filter content for only the best quality content.

    Args:
        content_iterator (Generator[Content, None, None]):
            The content iterator that provides content for filtering.

    Yields:
        Content: Only the best quality content grouped by the content id.
    """

    for _, grouped_content_iterator in groupby(content_iterator, key=lambda c: c.id):
        yield max(grouped_content_iterator, key=lambda c: c.quality)


def specific_content(
    content_iterator: Generator[Content, None, None], **conditions
) -> Generator[Content, None, None]:
    """Filter content by specific conditions.

    Args:
        content_iterator (Generator[Content, None, None]):
            The content iterator that provides content for filtering.

    Yields:
        Content: Only the content matching the provided conditions.
    """

    allowed_attributes = {"quality", "type"}

    filters = []
    for content_attribute, value in conditions.items():
        if content_attribute not in allowed_attributes:
            continue

        filters.append(lambda content: getattr(content, content_attribute, None) != value)

    yield from reduce(lambda f1, f2: lambda x: f2(f1(x)), filters, lambda x: x)(content_iterator)
