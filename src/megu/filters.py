"""This module provides basic content filters to wrap :func:`megu.iter_content` or alternatives."""

import warnings
from functools import partial, reduce
from itertools import groupby
from typing import Any, Generator

from megu.errors import MeguWarning
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

    def _filter_content(
        attribute: str,
        value: Any,
        iterator: Generator[Content, None, None],
    ) -> Generator[Content, None, None]:  # pragma: no cover
        yield from filter(lambda content: getattr(content, attribute, None) == value, iterator)

    allowed_attributes = {"quality", "type"}

    filters = []
    for content_attribute, value in conditions.items():
        if content_attribute not in allowed_attributes:
            warnings.warn(
                f"Skipping unhandled content filtering with attribute {content_attribute}, "
                f"allowed attributes are {allowed_attributes}",
                MeguWarning,
            )
            continue

        filters.append(partial(_filter_content, content_attribute, value))

    yield from reduce(lambda f1, f2: lambda x: f2(f1(x)), filters, lambda x: x)(content_iterator)
