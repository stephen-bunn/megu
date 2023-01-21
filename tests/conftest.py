from pytest import fixture

from megu.models import URL


@fixture
def megu_url(url: str | None = None) -> URL:
    return URL(url or "https://www.example.org/")
