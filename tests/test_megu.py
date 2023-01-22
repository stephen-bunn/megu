from hypothesis import given
from hypothesis.strategies import one_of

from megu import normalize_url
from megu.models import URL

from .strategies import DEFAULT_URL_STRAT, url


@given(one_of(url(), DEFAULT_URL_STRAT))
def test_normalize_url(url: str | URL):
    normalized = normalize_url(url)
    assert isinstance(normalized, URL)
