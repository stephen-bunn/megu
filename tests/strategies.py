import string
from datetime import datetime
from io import BytesIO
from pathlib import Path

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
    just,
    lists,
    none,
    one_of,
    sampled_from,
    text,
    uuids,
)

from megu.hash import HashType, hash_io
from megu.models import URL, Content, ContentChecksum, ContentMetadata, HTTPResource

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


@composite
def path(draw: DrawFn) -> Path:
    return Path(*draw(DEFAULT_NAME_STRAT))


@composite
def hash_type(draw: DrawFn, type_strat: SearchStrategy[HashType] | None = None) -> HashType:
    return draw(type_strat or sampled_from(HashType))


@composite
def hash_value(
    draw: DrawFn,
    type_strat: SearchStrategy[HashType] | None = None,
    content_strat: SearchStrategy[bytes] | None = None,
) -> str:
    _type = draw(hash_type(type_strat=type_strat))
    content = BytesIO(draw(content_strat or binary(min_size=1)))

    return hash_io(content, {_type})[_type]


@composite
def url(draw: DrawFn, url_strat: SearchStrategy[str] | None = None) -> URL:
    return URL(draw(url_strat or DEFAULT_URL_STRAT))


@composite
def http_resource(
    draw: DrawFn,
    method_strat: SearchStrategy[str] | None = None,
    url_strat: SearchStrategy[URL] | None = None,
    headers_strat: SearchStrategy[dict[str, str]] | None = None,
    content_strat: SearchStrategy[bytes] | None = None,
) -> HTTPResource:
    return HTTPResource(
        method=draw(
            method_strat
            or sampled_from(
                ["GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"]
            )
        ),
        url=draw(url_strat or DEFAULT_URL_STRAT),
        headers=draw(headers_strat or builds(dict)),
        content=draw(content_strat or none()),
    )


@composite
def content_checksum(
    draw: DrawFn,
    type_strat: SearchStrategy[HashType] | None = None,
    content_strat: SearchStrategy[bytes] | None = None,
) -> ContentChecksum:
    _type = draw(hash_type(type_strat=type_strat))
    return ContentChecksum(
        type=_type.value,
        value=draw(hash_value(type_strat=just(_type), content_strat=content_strat)),
    )


@composite
def content_metadata(
    draw: DrawFn,
    id_strat: SearchStrategy[str] | None = None,
    title_strat: SearchStrategy[str] | None = None,
    description_strat: SearchStrategy[str] | None = None,
    publisher_strat: SearchStrategy[str] | None = None,
    published_at_strat: SearchStrategy[datetime] | None = None,
    duration_strat: SearchStrategy[int] | None = None,
    filename_strat: SearchStrategy[str] | None = None,
    thumbnail_strat: SearchStrategy[URL] | None = None,
) -> ContentMetadata:
    optional_string_strat = one_of(text(), none())
    return ContentMetadata(
        id=draw(id_strat or optional_string_strat),
        title=draw(title_strat or optional_string_strat),
        description=draw(description_strat or optional_string_strat),
        publisher=draw(publisher_strat or optional_string_strat),
        published_at=draw(published_at_strat or one_of(datetimes(), none())),
        duration=draw(duration_strat or one_of(integers(min_value=0), none())),
        filename=draw(filename_strat or optional_string_strat),
        thumbnail=draw(thumbnail_strat or one_of(DEFAULT_URL_STRAT, none())),
    )


@composite
def content(
    draw: DrawFn,
    id_strat: SearchStrategy[str] | None = None,
    name_strat: SearchStrategy[str] | None = None,
    url_strat: SearchStrategy[URL] | None = None,
    quality_strat: SearchStrategy[float] | None = None,
    size_strat: SearchStrategy[int] | None = None,
    type_strat: SearchStrategy[str] | None = None,
    extension_strat: SearchStrategy[str] | None = None,
    resources_strat: SearchStrategy[list[HTTPResource]] | None = None,
    metadata_strat: SearchStrategy[ContentMetadata] | None = None,
    checksums_strat: SearchStrategy[list[ContentChecksum]] | None = None,
    extra_strat: SearchStrategy[dict] | None = None,
) -> Content:
    return Content(
        id=str(draw(id_strat or uuids(version=4))),
        name=draw(name_strat or DEFAULT_NAME_STRAT),
        url=draw(url_strat or url()),
        quality=draw(quality_strat or floats(min_value=0, allow_nan=False)),
        size=draw(size_strat or integers(min_value=1, max_value=1024)),
        type=draw(type_strat or DEFAULT_MIMETYPES_STRAT),
        extension=draw(extension_strat or one_of(from_regex(r"^\..+$"), none())),
        resources=draw(resources_strat or lists(http_resource(), min_size=1, max_size=2)),
        metadata=draw(metadata_strat or content_metadata()),
        checksums=draw(checksums_strat or lists(content_checksum(), max_size=2)),
        extra=draw(extra_strat or builds(dict)),
    )
