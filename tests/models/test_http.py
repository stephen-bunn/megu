# -*- encoding: utf-8 -*-
# Copyright (c) 2021 Stephen Bunn <stephen@bunn.io>
# ISC License <https://choosealicense.com/licenses/isc>

"""Contains tests for http model classes and types."""

from hypothesis import given
from hypothesis.strategies import builds
from requests import PreparedRequest, Request

from megu.models.http import HttpMethod, HttpResource

from ..strategies import megu_content
from .strategies import megu_http_resource, requests_request


@given(megu_http_resource())
def test_HttpResource_get_signature(resource: HttpResource):
    signature = resource._get_signature()
    assert isinstance(signature, bytes)
    assert len(signature) > 0


@given(megu_http_resource())
def test_HttpResource_fingerprint(resource: HttpResource):
    assert isinstance(resource.fingerprint, str)
    assert len(resource.fingerprint) > 0


@given(requests_request())
def test_HttpResource_from_request(request: Request):
    prepared_request = request.prepare()
    resource = HttpResource.from_request(prepared_request)
    assert isinstance(resource, HttpResource)
    assert str(resource.url).lower() == prepared_request.url.lower()  # type: ignore
    assert resource.method == HttpMethod(prepared_request.method) or HttpMethod.GET
    assert resource.headers == prepared_request.headers


@given(megu_http_resource(headers_strategy=builds(dict)))
def test_HttpResource_to_request(resource: HttpResource):
    request = resource.to_request()
    assert isinstance(request, PreparedRequest)
    assert request.method == resource.method.value
    assert request.url.lower() == str(resource.url).lower()  # type: ignore
