import re
from typing import Callable, Generator
from functools import partial, lru_cache

from rich.console import Console
from rich.theme import Theme
from glom import PathAccessError, glom
from glom.core import _MISSING as glom_MISSING

from megu.filters import best_content, specific_content
from megu.models import Content


@lru_cache(maxsize=1)
def get_console(color: bool | None) -> Console:
    return Console(
        theme=Theme(
            {
                "debug": "dim",
                "info": "cyan",
                "success": "green",
                "warning": "dim yellow",
                "error": "bold red",
                "repr.number": "cyan",
            },
        ),
        no_color=color is False,
    )


def build_content_filter(
    **conditions,
) -> Callable[[Generator[Content, None, None]], Generator[Content, None, None]]:
    if len(conditions) <= 0:
        return best_content

    filter_conditions = {key: value for key, value in conditions.items() if value is not None}
    if len(filter_conditions) <= 0:
        return best_content

    return partial(specific_content, **filter_conditions)


def build_content_name(content: Content, to_name: str, default: str | None = None) -> str:
    content_name = to_name
    for match in re.finditer(r"{(\w+(?:\.\w+)?)}", to_name):
        try:
            value = glom(content, match.group(1), default=(default or glom_MISSING))
            if value is None and default is None:
                raise ValueError(
                    f"Building name for content {content.id}, no value found for {match.group(1)!r}"
                )
            elif value is None:
                value = default

        except PathAccessError as exc:
            raise ValueError(f"Building name for content {content.id} failed") from exc

        content_name = re.sub(match.group(0), str(value), content_name)

    return content_name.strip()
