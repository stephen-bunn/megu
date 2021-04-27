# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""This module provides simple safe hashing functions.

We only support several of the available hashing algorithms from :mod:`hashlib` as
they have several that are never really used (such as ``sha224``). However, we do supply
support for `xxhash <https://cyan4973.github.io/xxHash/>`_ as we typically will be
calculating checksums for files >1GB which is safe and **very** fast using xxhash.

.. tip:: The provided basic functions allow you to calculate multiple hashes at the same
    time which means that your bottleneck will be whatever slowest hashing algorithm you
    request.

>>> from megu.hasher import hash_io, HashType
>>> with open("/home/user/A/PATH/TO/A/FILE", "rb") as file_io:
...     hashes = hash_io(file_io, {HashType.MD5, HashType.XXHASH})
{
    <HashType.XXHASH: 'xxhash'>: '59af876b8f4b8998',
    <HashType.MD5: 'md5'>: 'a46062d24103b87560b2dc0887a1d5de'
}

Attributes:
    DEFAULT_CHUNK_SIZE (int):
        The default size in bytes to chunk file streams for hashing.
"""

import hashlib
from enum import Enum
from pathlib import Path
from typing import IO, BinaryIO, Callable, Dict, Set, Union

import xxhash

from .log import instance as log

Hasher_T = Callable[[Union[bytes, bytearray, memoryview]], "hashlib._Hash"]

DEFAULT_CHUNK_SIZE = 2 ** 16


class HashType(Enum):
    """Enumeration of supported hash types."""

    XXHASH = "xxhash"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"
    BLAKE2S = "blake2s"

    # NOTE: Enums still consider class-mangled class properties as values in the
    # enumeration. So you can do HashType._HashType__available_hashers or
    # HashType("__available_hashers") and it's *technically* valid.
    __available_hashers: Dict[str, Hasher_T] = {
        XXHASH: xxhash.xxh64,
        MD5: hashlib.md5,
        SHA1: hashlib.sha1,
        SHA256: hashlib.sha256,
        SHA512: hashlib.sha512,
        BLAKE2B: hashlib.blake2b,
        BLAKE2S: hashlib.blake2s,
    }

    @property
    def hasher(self) -> Hasher_T:
        """Get the hasher callable for the current hash type."""

        # The type of this __available_hashers is no longer a dict due to it being
        # coerced into a enumeration property on the instance. That is why we are having
        # to access it through .value here.
        return self.__available_hashers.value[self.value]  # type: ignore


def hash_io(
    io: Union[BinaryIO, IO[bytes]],
    types: Set[HashType],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Dict[HashType, str]:
    """Calculate the requested hash types for some given binary IO instance.

    >>> from io import BytesIO
    >>> from megu.hasher import hash_io, HashType
    >>> hash_io(BytesIO(b"Hey, I'm a string"), {HashType("xxhash"), HashType.MD5})
    {
        <HashType.XXHASH: 'xxhash'>: 'd299da7e31fb9c47',
        <HashType.MD5: 'md5'>: '25cb7b2c4e2064c1deebac4b66195c9c'
    }

    Of course if you need to instead hash :class:`~io.StringIO`, it's up to you to
    do whatever conversions you need to do to create a :class:`~io.BytesIO` instance.
    This typically involves having to read the entire string and encode it.

    >>> from io import BytesIO, StringIO
    >>> from megu.hasher import hash_io, HashType
    >>> string_io = StringIO("Hey, I'm a string")
    >>> byte_io = BytesIO(string_io.read().encode("utf-8"))
    >>> hash_io(byte_io, {HashType.XXHASH, HashType("md5")})
    {
        <HashType.XXHASH: 'xxhash'>: 'd299da7e31fb9c47',
        <HashType.MD5: 'md5'>: '25cb7b2c4e2064c1deebac4b66195c9c'
    }

    Args:
        io (~typing.BinaryIO):
            The IO to calculate hashes for.
        types (Set[~HashType]):
            The set of names for hash types to calculate.
        chunk_size (int):
            The size of bytes to have loaded from the buffer into memory at a time.
            Defaults to :attr:`~DEFAULT_CHUNK_SIZE`.

    Raises:
        ValueError:
            If one of the given types is not supported.

    Returns:
        Dict[~HashType, str]:
            A dictionary of hash type strings and the calculated hexdigest of the hash.
    """

    log.debug(f"Hashing {io!r} with types {types!r} at chunks of {chunk_size!r} bytes")
    hashers: Dict[HashType, "hashlib._Hash"] = {
        hash_type: hash_type.hasher() for hash_type in types  # type: ignore
    }

    chunk: bytes = io.read(chunk_size)
    while chunk:
        for hash_instance in hashers.values():
            hash_instance.update(chunk)
        chunk = io.read(chunk_size)

    return {key: value.hexdigest() for key, value in hashers.items()}


def hash_file(
    filepath: Path,
    types: Set[HashType],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Dict[HashType, str]:
    """Calculate the requested hash types for some given file path instance.

    Basic usage of this function typically looks like the following:

    >>> from pathlib import Path
    >>> from megu.hasher import hash_file, HashType
    >>> big_file_path = Path("/home/USER/A/PATH/TO/A/BIG/FILE")
    >>> hash_file(big_file_path, {HashType("md5"), HashType.XXHASH})
    {
        <HashType.XXHASH: 'xxhash'>: '59af876b8f4b8998',
        <HashType.MD5: 'md5'>: 'a46062d24103b87560b2dc0887a1d5de'
    }

    Args:
        filepath (~pathlib.Path):
            The filepath to calculate hashes for.
        types (Set[~HashType]):
            The set of names for hash types to calculate.
        chunk_size (int):
            The size of bytes ot have loaded from the file into memory at a time.
            Defaults to ``DEFAULT_CHUNK_SIZE``.

    Raises:
        FileNotFoundError:
            If the given filepath does not point to an existing file.
        ValueError:
            If one of the given types is not supported.

    Returns:
        Dict[~HashType, str]:
            A dictionary of hash type strings and the calculated hexdigest of the hash.
    """

    if not filepath.is_file():
        raise FileNotFoundError(f"No such file {filepath!s} exists")

    with filepath.open("rb") as file_io:
        return hash_io(io=file_io, types=types, chunk_size=chunk_size)  # type: ignore
