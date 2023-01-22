import pytest
from hypothesis import given
from hypothesis.strategies import lists, sampled_from

from megu.errors import MeguWarning
from megu.filters import best_content, specific_content
from megu.models import Content

from .strategies import content


@given(
    lists(
        content(id_strat="test", quality_strat=sampled_from([0, 1])),
        min_size=1,
        max_size=3,
    )
)
def test_best_content(content_list: list[Content]):
    content = next(best_content(iter(content_list)))  # type: ignore
    assert content.quality == max(c.quality for c in content_list)


@given(
    content(id_strat="test_a", quality_strat=sampled_from([0, 1])),
    content(id_strat="test_b", quality_strat=sampled_from([0, 1])),
)
def test_best_content_yields_content_from_multiple_ids(content_a: Content, content_b: Content):
    content_items = list(best_content(iter([content_a, content_b])))  # type: ignore
    assert len(content_items) == 2


def test_best_content_raises_StopIteration_for_no_content():
    with pytest.raises(StopIteration):
        next(best_content(iter([])))  # type: ignore


@given(content(quality_strat=0), content(quality_strat=1), sampled_from([0, 1]))
def test_specific_content_filters_on_quality(
    content_a: Content, content_b: Content, content_quality: float
):
    assert (
        next(
            specific_content(iter([content_a, content_b]), quality=content_quality)  # type: ignore
        ).quality
        == content_quality
    )


@given(
    content(type_strat="audio/mpeg"),
    content(type_strat="video/mp4"),
    sampled_from(["audio/mpeg", "video/mp4"]),
)
def test_specific_content_filters_on_type(
    content_a: Content, content_b: Content, content_type: str
):
    assert (
        next(specific_content(iter([content_a, content_b]), type=content_type)).type  # type: ignore
        == content_type
    )


def test_specific_content_warns_for_unallowed_attributes():
    with pytest.raises(StopIteration), pytest.warns(MeguWarning) as warn_records:
        next(specific_content(iter([]), test="test"))  # type: ignore
        assert "Skipping unhandled content filtering with attribute test" in str(
            warn_records[0].message
        )
