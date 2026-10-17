import json

import pytest
from pydantic import ValidationError
from requests import Request, Response

from api_testing.assertions import (
    KnownPayloadValidationGap,
    assert_fields,
    assert_invalid_payload_rejected,
    assert_model,
)
from api_testing.models import Post

pytestmark = pytest.mark.unit


def make_response(status: int, data: object, content_type: str = "application/json") -> Response:
    response = Response()
    response.status_code = status
    response._content = json.dumps(data).encode()
    response.headers["Content-Type"] = content_type
    response.url = "https://example.com/posts"
    response.request = Request("POST", response.url).prepare()
    return response


@pytest.mark.parametrize("invalid_id", ["1", True, 1.5])
def test_response_model_does_not_coerce_invalid_types(invalid_id) -> None:
    with pytest.raises(ValidationError):
        Post.model_validate({"id": invalid_id, "userId": 1, "title": "Title", "body": "Body"})


def test_field_assertion_distinguishes_boolean_from_integer() -> None:
    with pytest.raises(AssertionError, match="Field 'userId'"):
        assert_fields({"userId": True}, {"userId": 1})


def test_schema_error_is_reported_as_readable_assertion() -> None:
    response = make_response(200, {"id": 1})
    with pytest.raises(AssertionError, match="Invalid Post schema"):
        assert_model(response, Post)


def test_only_verified_invalid_payload_acceptance_is_a_known_gap() -> None:
    response = make_response(201, {"id": 101, "title": 42})
    with pytest.raises(KnownPayloadValidationGap):
        assert_invalid_payload_rejected(response, {"title": 42})


@pytest.mark.parametrize("status", [200, 403, 404, 500, 503])
def test_unexpected_status_is_not_hidden_as_known_validation_gap(status: int) -> None:
    response = make_response(status, {"error": "unexpected"})
    with pytest.raises(AssertionError) as error:
        assert_invalid_payload_rejected(response, {})

    assert type(error.value) is AssertionError


@pytest.mark.parametrize(
    ("data", "content_type"),
    [
        ({"id": 101, "error": "unexpected"}, "application/json"),
        ({"id": "101"}, "application/json"),
        ({"id": 101}, "text/html"),
        ([], "application/json"),
    ],
)
def test_unexpected_created_response_is_not_hidden_as_known_gap(data, content_type) -> None:
    response = make_response(201, data, content_type)
    with pytest.raises(AssertionError) as error:
        assert_invalid_payload_rejected(response, {})

    assert type(error.value) is AssertionError


@pytest.mark.parametrize("status", [400, 422])
def test_validation_error_response_satisfies_desired_contract(status: int) -> None:
    assert_invalid_payload_rejected(make_response(status, {"error": "invalid input"}), {})
