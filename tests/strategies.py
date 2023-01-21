import string
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import TypeAlias, TypeVar

from hypothesis.provisional import urls
from hypothesis.strategies import (
    DrawFn,
    SearchStrategy,
    binary,
    builds,
    composite,
    datetimes,
    floats,
    from_regex,
    integers,
    lists,
    none,
    one_of,
    sampled_from,
    text,
    uuids,
)

from megu.hash import HashType, hash_io
from megu.models import (
    URL,
    Content,
    ContentChecksum,
    ContentManifest,
    ContentMetadata,
    HTTPResource,
)

DEFAULT_URL_STRAT = urls().filter(lambda x: ":0" not in x)
DEFAULT_NAME_STRAT = text(string.ascii_letters + string.digits, min_size=1, max_size=20)
DEFAULT_MIMETYPES_STRAT = sampled_from(
    [
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
    ]
)

T = TypeVar("T")
Strat: TypeAlias = T | SearchStrategy[T] | None


def _draw(draw: DrawFn, strat: Strat[T], fallback: SearchStrategy[T]) -> T:
    if not isinstance(strat, SearchStrategy):
        return draw(fallback) if strat is None else strat

    return draw(strat)


@composite
def path(draw: DrawFn) -> Path:
    return Path(*draw(DEFAULT_NAME_STRAT))


@composite
def hash_type(draw: DrawFn, type_strat: Strat[HashType] = None) -> HashType:
    return _draw(draw, type_strat, sampled_from(HashType))


@composite
def hash_value(
    draw: DrawFn,
    type_strat: Strat[HashType] = None,
    content_strat: Strat[bytes] = None,
) -> str:
    _type = draw(hash_type(type_strat))
    content = BytesIO(_draw(draw, content_strat, binary(min_size=1)))

    return hash_io(content, {_type})[_type]


@composite
def url(draw: DrawFn, url_strat: Strat[str] = None) -> URL:
    return URL(_draw(draw, url_strat, DEFAULT_URL_STRAT))


@composite
def http_resource(
    draw: DrawFn,
    method_strat: Strat[str] = None,
    url_strat: Strat[URL] = None,
    headers_strat: Strat[dict[str, str]] = None,
    content_strat: Strat[bytes | None] = None,
) -> HTTPResource:
    return HTTPResource(
        method=_draw(
            draw,
            method_strat,
            sampled_from(
                ["GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"]
            ),
        ),
        url=_draw(draw, url_strat, DEFAULT_URL_STRAT),
        headers=_draw(draw, headers_strat, builds(dict)),
        content=_draw(draw, content_strat, none()),
    )


@composite
def content_checksum(
    draw: DrawFn,
    type_strat: Strat[HashType] = None,
    content_strat: Strat[bytes] = None,
) -> ContentChecksum:
    _type = draw(hash_type(type_strat))
    return ContentChecksum(
        type=_type.value,
        value=draw(hash_value(type_strat=_type, content_strat=content_strat)),
    )


@composite
def content_metadata(
    draw: DrawFn,
    id_strat: Strat[str | None] = None,
    title_strat: Strat[str | None] = None,
    description_strat: Strat[str | None] = None,
    publisher_strat: Strat[str | None] = None,
    published_at_strat: Strat[datetime | None] = None,
    duration_strat: Strat[int | None] = None,
    filename_strat: Strat[str | None] = None,
    thumbnail_strat: Strat[URL | None] = None,
) -> ContentMetadata:
    optional_string_strat = one_of(text(), none())
    return ContentMetadata(
        id=_draw(draw, id_strat, optional_string_strat),
        title=_draw(draw, title_strat, optional_string_strat),
        description=_draw(draw, description_strat, optional_string_strat),
        publisher=_draw(draw, publisher_strat, optional_string_strat),
        published_at=_draw(draw, published_at_strat, one_of(datetimes(), none())),
        duration=_draw(draw, duration_strat, one_of(integers(min_value=0), none())),
        filename=_draw(draw, filename_strat, optional_string_strat),
        thumbnail=_draw(draw, thumbnail_strat, one_of(DEFAULT_URL_STRAT, none())),
    )


@composite
def content(
    draw: DrawFn,
    id_strat: Strat[str] | None = None,
    name_strat: Strat[str] | None = None,
    url_strat: Strat[URL] | None = None,
    quality_strat: Strat[float] | None = None,
    size_strat: Strat[int] | None = None,
    type_strat: Strat[str] | None = None,
    extension_strat: Strat[str | None] = None,
    resources_strat: Strat[list[HTTPResource]] = None,
    metadata_strat: Strat[ContentMetadata | None] = None,
    checksums_strat: Strat[list[ContentChecksum]] = None,
    extra_strat: Strat[dict] = None,
) -> Content:
    return Content(
        id=str(_draw(draw, id_strat, uuids(version=4))),
        name=_draw(draw, name_strat, DEFAULT_NAME_STRAT),
        url=_draw(draw, url_strat, url()),
        quality=_draw(draw, quality_strat, floats(min_value=0, allow_nan=False)),
        size=_draw(draw, size_strat, integers(min_value=1, max_value=1024)),
        type=_draw(draw, type_strat, DEFAULT_MIMETYPES_STRAT),
        extension=_draw(
            draw, extension_strat, one_of(from_regex(r"^\.[a-zA-Z0-9]{1,10}$"), none())
        ),
        resources=_draw(draw, resources_strat, lists(http_resource(), min_size=1, max_size=2)),
        metadata=_draw(draw, metadata_strat, content_metadata()),
        checksums=_draw(draw, checksums_strat, lists(content_checksum(), max_size=2)),
        extra=_draw(draw, extra_strat, builds(dict)),
    )


@composite
def content_manifest_artifact(
    draw: DrawFn,
    id_strat: Strat[str] | None = None,
    path_strat: Strat[Path] | None = None,
) -> tuple[str, Path]:
    return (
        _draw(draw, id_strat, DEFAULT_NAME_STRAT),
        _draw(draw, path_strat, path()),
    )


@composite
def content_manifest(
    draw: DrawFn,
    id_strat: Strat[str] | None = None,
    artifacts_strat: Strat[list[tuple[str, Path]]] | None = None,
) -> ContentManifest:
    return (
        _draw(draw, id_strat, DEFAULT_NAME_STRAT),
        _draw(draw, artifacts_strat, lists(content_manifest_artifact(), min_size=1, max_size=4)),
    )
