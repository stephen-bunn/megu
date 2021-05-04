# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains some really basic content filters."""

from functools import partial
from itertools import groupby
from typing import Any, Callable, Dict, Iterable, List

from .log import instance as log
from .models import Content
from .utils import compose_functions


def best_content(content: Iterable[Content]) -> Iterable[Content]:
    """Get the best quality content from the extracted content iterator.

    Args:
        content (Iterable[~models.content.Content]):
            The iterable of content that was extracted

    Returns:
        ~models.content.Content:
            The highest quality content
    """

    for _, content_items in groupby(content, key=lambda c: c.id):
        yield max(content_items, key=lambda c: c.quality)


def _filter_type(type: str, content_iterator: Iterable[Content]) -> Iterable[Content]:
    """Filter out content that does not match the provided type.

    Args:
        type (str):
            The desired type of content.
        content_iterator (Iterable[Content]):
            The content iterable that should be filtered.

    Returns:
        Iterable[Content]:
            An iterator for type filtered content.

    Yields:
        Content:
            Content filtered to match the provided type.
    """

    for content in content_iterator:
        if content.type != type:
            log.debug(
                f"Filtering out content {content} due to mismatched type "
                f"({content.type!r} != {type!r})"
            )
            continue

        yield content


def _filter_quality(
    quality: float, content_iterator: Iterable[Content]
) -> Iterable[Content]:
    """Filter out content that does not match the provided quality.

    Args:
        quality (float):
            The desired quality of content.
        content_iterator (Iterable[Content]):
            The content iterable that should be filtered.

    Returns:
        Iterable[Content]:
            An iterator for quality filtered content.

    Yields:
        Content:
            Content filtered to match the provided quality.
    """

    for content in content_iterator:
        if content.quality != quality:
            log.debug(
                f"Filtering out content {content} due to mismatched quality "
                f"({content.quality!r} != {quality!r})"
            )
            continue

        yield content


def specific_content(content: Iterable[Content], **conditions) -> Iterable[Content]:
    """Apply many filters to an iterable of content instances.

    With no conditions provided, no content will be filtered out and all content
    instances will be returned.
    When conditions are provided, matching filter handlers will be dynamically applied
    to filter out content instances.

    Args:
        content (Iterable[Content]):
            An iterable of content to apply many filters to.
        conditions (Dict[str, Any]):
            A dictionary of filters to apply to the given content iterable.

    Returns:
        Iterable[Content]:
            An iterator for filtered content.

    Yields:
        Content:
            Content instances which have passed all defined filters.
    """

    handlers: Dict[str, Callable[[Any, Iterable[Content]], Iterable[Content]]] = {
        "quality": _filter_quality,
        "type": _filter_type,
    }

    filters: List[Callable[[Iterable[Content]], Iterable[Content]]] = []
    for key, value in conditions.items():
        if key not in handlers:
            log.warning(f"No such content filter for key {key!r} is defined")
            continue

        filters.append(partial(handlers[key], value))

    yield from compose_functions(*filters)(content)
