from io import BytesIO
from pathlib import Path
from tempfile import mkstemp

import pytest
from hypothesis import assume, given
from hypothesis.strategies import binary, integers, sets

from megu.hash import DEFAULT_CHUNK_SIZE, HashType, hash_file, hash_io

from .strategies import hash_type, path


@given(binary(), sets(hash_type()), integers(min_value=1, max_value=DEFAULT_CHUNK_SIZE))
def test_hash_io(content: bytes, hash_types: set[HashType], chunk_size: int):
    result = hash_io(io=BytesIO(content), types=hash_types, chunk_size=chunk_size)
    assert isinstance(result, dict)
    assert len(result) == len(hash_types)

    for hash_type, hash_value in result.items():
        assert isinstance(hash_type, HashType)
        assert isinstance(hash_value, str)

        assert hash_type.hasher(content).hexdigest() == hash_value


@given(binary(), sets(hash_type()), integers(min_value=1, max_value=DEFAULT_CHUNK_SIZE))
def test_hash_file(content: bytes, hash_types: set[HashType], chunk_size: int):
    _, temp_name = mkstemp()
    with open(temp_name, "wb") as file_io:
        file_io.write(content)

    try:
        temp_filepath = Path(temp_name).resolve()
        result = hash_file(filepath=temp_filepath, types=hash_types, chunk_size=chunk_size)
        assert isinstance(result, dict)
        assert len(result) == len(hash_types)

        for hash_type, hash_value in result.items():
            assert isinstance(hash_type, HashType)
            assert isinstance(hash_value, str)

            assert hash_type.hasher(content).hexdigest() == hash_value

    finally:
        try:
            temp_filepath.unlink()
        except PermissionError:
            # NOTE: typically occurs on windows when running tests in parallel, but
            # since we are creating these in a temporary directory it shouldn't really
            # matter if we can fully remove the link to this file
            pass


@given(path(), sets(hash_type()), integers(min_value=1, max_value=DEFAULT_CHUNK_SIZE))
def test_hash_file_raises_FileNotFoundError_with_missing_file(
    filepath: Path, hash_types: set[HashType], chunk_size: int
):
    assume(filepath.is_file() is False)
    with pytest.raises(FileNotFoundError):
        hash_file(filepath=filepath, types=hash_types, chunk_size=chunk_size)
