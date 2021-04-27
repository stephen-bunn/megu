# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# GPLv3 License <https://choosealicense.com/licenses/gpl-3.0/>

"""Contains custom model types to be used in model implementations."""

from __future__ import annotations

from typing import Any, Callable, Dict, Generator

from furl.furl import furl
from pydantic import AnyHttpUrl, BaseConfig
from pydantic.fields import ModelField


class Url(furl):
    """A URL validated by :class:`~pydantic.AnyHttpUrl` and casted as a ``furl``."""

    min_length = 1
    max_length = 2 ** 16

    @classmethod
    def __get_validators__(
        cls,
    ) -> Generator[Callable[[Any, ModelField, BaseConfig], Any], None, None]:
        """Yield the appropriate validators for the class.

        Yields:
            Callable[[Any, ModelField, BaseConfig], Any]:
                A validator callable.
        """

        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        """Modify the field schema entry.

        Args:
            field_schema (Dict[str, Any]):
                The current field schema.
        """

        AnyHttpUrl.__modify_schema__(field_schema)

    @classmethod
    def validate(cls, value: Any, field: ModelField, config: BaseConfig) -> furl:
        """Validate and parse the given URL string value.

        Args:
            value (Any):
                The URL provided by a user.
            field (ModelField):
                The field instance the URL is using.
            config (BaseConfig):
                The config instance the URL is in.

        Returns:
            :class:`furl.furl.furl`:
                The furl instance of the given URL string.
        """

        AnyHttpUrl.validate(value, field, config)
        return furl(url=value)
