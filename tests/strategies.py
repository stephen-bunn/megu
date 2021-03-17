# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for packaging testing."""


from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from hypothesis.strategies import (
    SearchStrategy,
    binary,
    booleans,
    builds,
    complex_numbers,
    composite,
    floats,
    from_regex,
    integers,
    lists,
    none,
    one_of,
    sampled_from,
    text,
)

from megu.hasher import HashType, hash_io


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
