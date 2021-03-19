# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for packaging testing."""


from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from hypothesis.provisional import urls
from hypothesis.strategies import (
    SearchStrategy,
    binary,
    booleans,
    builds,
    complex_numbers,
    composite,
    datetimes,
    floats,
    from_regex,
    integers,
    just,
    lists,
    none,
    one_of,
    sampled_from,
    text,
    uuids,
)
from requests import Request

from megu.hasher import HashType, hash_io
from megu.models import Checksum, Content, HttpMethod, HttpResource, Meta, Url
from megu.models.content import Resource

VALID_MIMETYPES = (
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/svg+xml",
    "image/tiff",
    "image/webp",
    "video/mpeg",
    "video/ogg",
    "video/mp2t",
    "video/webm",
    "video/3gpp",
    "video/3gpp2",
    "video/x-msvideo",
    "audio/midi",
    "audio/x-midi",
    "audio/mpeg",
    "audio/ogg",
    "audio/opus",
    "audio/wav",
    "audio/webm",
    "audio/3gpp",
    "audio/3gpp2",
    "audio/acc",
)


@composite
def builtin_types(
    draw, include: Optional[List[Type]] = None, exclude: Optional[List[Type]] = None
) -> Any:
    """Composite strategy for building an instance of a builtin type.

    This strategy allows you to check against builtin types for when you need to do
    variable validation (which should be rare). By default this composite will generate
    all available types of builtins, however you can either tell it to only generate
    some types or exclude some types. You do this using the ``include`` and ``exclude``
    parameters.

    For example using the ``include`` parameter like the following will ONLY generate
    strings and floats for the samples:

    >>> @given(builtin_types(include=[str, float]))
    ... def test_only_strings_and_floats(value: Union[str, float]):
    ...     assert isinstance(value, (str, float))

    Similarly, you can specify to NOT generate Nones and complex numbers like the
    following example:

    >>> @given(builtin_types(exclude=[None, complex]))
    ... def test_not_none_or_complex(value: Any):
    ...     assert value and not isinstance(value, complex)
    """

    strategies: Dict[Any, SearchStrategy[Any]] = {
        None: none(),
        int: integers(),
        bool: booleans(),
        float: floats(allow_nan=False),
        tuple: builds(tuple),
        list: builds(list),
        set: builds(set),
        frozenset: builds(frozenset),
        str: text(),
        bytes: binary(),
        complex: complex_numbers(),
    }

    to_use = set(strategies.keys())
    if include and len(include) > 0:
        to_use = set(include)

    if exclude and len(exclude) > 0:
        to_use = to_use - set(exclude)

    return draw(
        one_of([strategy for key, strategy in strategies.items() if key in to_use])
    )


@composite
def pythonic_name(draw, name_strategy: Optional[SearchStrategy[str]] = None) -> str:
    """Composite strategy for building a Python valid variable / class name."""

    return draw(
        from_regex(r"\A[a-zA-Z]+[a-zA-Z0-9\_]*\Z")
        if not name_strategy
        else name_strategy
    )


@composite
def pathlib_path(draw) -> Path:
    """Composite strategy for building a random ``pathlib.Path`` instance."""

    return Path(*draw(lists(pythonic_name(), min_size=1)))


HashType_strategy = sampled_from(HashType).filter(
    lambda hash_type: hash_type != HashType._HashType__available_hashers  # type: ignore
)


@composite
def hash_type(
    draw, hash_type_strategy: Optional[SearchStrategy[HashType]] = None
) -> HashType:
    """Composite strategy for fetching a :class:`~megu.hasher.HashType`."""

    return draw(HashType_strategy if not hash_type_strategy else hash_type_strategy)


@composite
def hash_hexdigest(
    draw,
    hash_type_strategy: Optional[SearchStrategy[HashType]] = None,
    content_strategy: Optional[SearchStrategy[bytes]] = None,
) -> str:
    """Composite strategy for building a hash hexdigest."""

    type_ = draw(hash_type(hash_type_strategy=hash_type_strategy))
    content = BytesIO(
        draw(binary(min_size=1) if not content_strategy else content_strategy)
    )
    return hash_io(content, {type_})[type_]


@composite
def requests_request(
    draw,
    method_strategy: Optional[SearchStrategy[str]] = None,
    url_strategy: Optional[SearchStrategy[str]] = None,
    headers_strategy: Optional[SearchStrategy[dict]] = None,
) -> Request:
    """Composite strategy for building a basic requests Request instance."""

    return Request(
        method=draw(
            method_strategy
            if method_strategy
            else sampled_from(list(HttpMethod.__members__.keys()))
        ),
        url=draw(url_strategy if url_strategy else urls()),
        headers=draw(headers_strategy if headers_strategy else builds(dict)),
    )


@composite
def megu_url(draw, url_strategy: Optional[SearchStrategy[str]] = None) -> Url:
    """Composite strategy for building a megu Url model."""

    return Url(draw(url_strategy if url_strategy else urls()))


@composite
def megu_checksum(
    draw,
    type_strategy: Optional[SearchStrategy[HashType]] = None,
    hash_strategy: Optional[SearchStrategy[bytes]] = None,
) -> Checksum:
    """Composite strategy for building a megu Checksum model."""

    type_ = draw(hash_type(hash_type_strategy=type_strategy))
    return Checksum(
        type=type_,
        hash=draw(
            hash_hexdigest(
                hash_type_strategy=just(type_),
                content_strategy=hash_strategy,
            )
        ),
    )


@composite
def megu_meta(
    draw,
    id_strategy: Optional[SearchStrategy[str]] = None,
    title_strategy: Optional[SearchStrategy[str]] = None,
    description_strategy: Optional[SearchStrategy[str]] = None,
    publisher_strategy: Optional[SearchStrategy[str]] = None,
    published_at_strategy: Optional[SearchStrategy[datetime]] = None,
    duration_strategy: Optional[SearchStrategy[int]] = None,
    filename_strategy: Optional[SearchStrategy[str]] = None,
    thumbnail_strategy: Optional[SearchStrategy[str]] = None,
) -> Meta:
    """Composite strategy for building a megu Meta model."""

    optional_str_strategy = one_of(text(), none())
    return Meta(
        id=draw(id_strategy if id_strategy else optional_str_strategy),
        title=draw(title_strategy if title_strategy else optional_str_strategy),
        description=draw(
            description_strategy if description_strategy else optional_str_strategy
        ),
        publisher=draw(
            publisher_strategy if publisher_strategy else optional_str_strategy
        ),
        published_at=draw(
            published_at_strategy
            if published_at_strategy
            else one_of(datetimes() or none())
        ),
        duration=draw(
            duration_strategy
            if duration_strategy
            else one_of(integers(min_value=0), none())
        ),
        filename=draw(
            filename_strategy if filename_strategy else optional_str_strategy
        ),
        thumbnail=draw(
            thumbnail_strategy if thumbnail_strategy else one_of(urls(), none())
        ),
    )


@composite
def megu_http_resource(
    draw,
    method_strategy: Optional[SearchStrategy[HttpMethod]] = None,
    url_strategy: Optional[SearchStrategy[str]] = None,
    headers_strategy: Optional[SearchStrategy[Dict[str, str]]] = None,
    data_strategy: Optional[SearchStrategy[bytes]] = None,
    auth_strategy: Optional[SearchStrategy[Callable[[Request], Request]]] = None,
) -> HttpResource:
    """Composite strategy for building a megu HttpResource model."""

    return HttpResource(
        method=draw(method_strategy if method_strategy else sampled_from(HttpMethod)),
        url=draw(url_strategy if url_strategy else urls()),
        headers=draw(headers_strategy if headers_strategy else builds(dict)),
        data=draw(data_strategy if data_strategy else none()),
        auth=draw(auth_strategy if auth_strategy else none()),
    )


@composite
def megu_content(
    draw,
    id_strategy: Optional[SearchStrategy[str]] = None,
    url_strategy: Optional[SearchStrategy[str]] = None,
    quality_strategy: Optional[SearchStrategy[float]] = None,
    size_strategy: Optional[SearchStrategy[int]] = None,
    type_strategy: Optional[SearchStrategy[str]] = None,
    extension_strategy: Optional[SearchStrategy[str]] = None,
    resources_strategy: Optional[SearchStrategy[List[Resource]]] = None,
    meta_strategy: Optional[SearchStrategy[Meta]] = None,
    checksum_strategy: Optional[SearchStrategy[List[Checksum]]] = None,
    extra_strategy: Optional[SearchStrategy[dict]] = None,
) -> Content:
    """Composite strategy for building a megu Content model."""

    return Content(
        id=str(draw(id_strategy if id_strategy else uuids(version=4))),
        url=draw(url_strategy if url_strategy else urls()),
        quality=draw(
            quality_strategy
            if quality_strategy
            else floats(min_value=0, allow_nan=False)
        ),
        size=draw(
            size_strategy if size_strategy else integers(min_value=1, max_value=1024)
        ),
        type=draw(type_strategy if type_strategy else sampled_from(VALID_MIMETYPES)),
        extension=draw(
            extension_strategy
            if extension_strategy
            else one_of(from_regex(r"^\..+$"), none())
        ),
        resources=draw(
            resources_strategy
            if resources_strategy
            else lists(megu_http_resource(), min_size=1, max_size=2),
        ),
        meta=draw(meta_strategy if meta_strategy else megu_meta()),
        checksums=draw(
            checksum_strategy
            if checksum_strategy
            else lists(megu_checksum(), max_size=2)
        ),
        extra=draw(extra_strategy if extra_strategy else builds(dict)),
    )
