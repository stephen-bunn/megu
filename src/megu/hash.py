"""This module provides simple safe hashing functions.

We only support several of the available hashing algorithms from :mod:`hashlib` as
they have several that are never really used (such as ``sha224``).

The provided basic functions allow you to calculate multiple hashes at the same
time which means that your bottleneck will be whatever slowest hashing algorithm you
request.

```python
from megu.hasher import hash_io, HashType
with open("/home/user/A/PATH/TO/A/FILE", "rb") as file_io:
    hashes = hash_io(file_io, {HashType.MD5, HashType.SHA256})

# {
#     <HashType.SHA256: 'sha256'>: 'f0e4c2f76c58916ec258f246851bea091d14d4247a2f...',
#     <HashType.MD5: 'md5'>: 'a46062d24103b87560b2dc0887a1d5de'
# }
```

Attributes:
    DEFAULT_CHUNK_SIZE (int):
        The default size in bytes to chunk file streams for hashing.
"""

import hashlib
from enum import Enum
from pathlib import Path
from typing import IO, BinaryIO, Callable

Hasher = Callable[[bytes | bytearray | memoryview], "hashlib._Hash"]

DEFAULT_CHUNK_SIZE = 2**16
AVAILABLE_HASHERS: dict[str, Hasher] = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}


class HashType(Enum):
    """Enumeration of supported hash types."""

    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"

    @property
    def hasher(self) -> Hasher:
        """Get the hasher callable for the current hash type."""

        if self.value not in AVAILABLE_HASHERS:
            raise ValueError(f"No available hasher {self.value!r}")

        return AVAILABLE_HASHERS[self.value]


def hash_io(
    io: BinaryIO | IO[bytes],
    types: set[HashType],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict[HashType, str]:
    """Calculate the requested hash types for some given binary IO instance.

    >>> from io import BytesIO
    >>> from megu.hasher import hash_io, HashType
    >>> hash_io(BytesIO(b"Hey, I'm a string"), {HashType("sha256"), HashType.MD5})
    {
        <HashType.SHA256: 'sha256'>: 'f0e4c2f76c58916ec258f246851bea091d14d4247a2f...',
        <HashType.MD5: 'md5'>: '25cb7b2c4e2064c1deebac4b66195c9c'
    }

    Of course if you need to instead hash :class:`~io.StringIO`, it's up to you to
    do whatever conversions you need to do to create a :class:`~io.BytesIO` instance.
    This typically involves having to read the entire string and encode it.

    >>> from io import BytesIO, StringIO
    >>> from megu.hasher import hash_io, HashType
    >>> string_io = StringIO("Hey, I'm a string")
    >>> byte_io = BytesIO(string_io.read().encode("utf-8"))
    >>> hash_io(byte_io, {HashType.SHA256, HashType("md5")})
    {
        <HashType.SHA256: 'sha256'>: 'f0e4c2f76c58916ec258f246851bea091d14d4247a2f...',
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

    hashers: dict[HashType, "hashlib._Hash"] = {
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
    types: set[HashType],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict[HashType, str]:
    """Calculate the requested hash types for some given file path instance.

    Basic usage of this function typically looks like the following:

    >>> from pathlib import Path
    >>> from megu.hasher import hash_file, HashType
    >>> big_file_path = Path("/home/USER/A/PATH/TO/A/BIG/FILE")
    >>> hash_file(big_file_path, {HashType("md5"), HashType.SHA256})
    {
        <HashType.SHA256: 'sha256'>: 'f0e4c2f76c58916ec258f246851bea091d14d4247a2f...',
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
