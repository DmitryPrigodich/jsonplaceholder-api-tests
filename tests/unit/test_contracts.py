import json

import pytest
from pydantic import ValidationError
from requests import Request, Response

from api_testing.assertions import assert_model, assert_status
from api_testing.models import Post, PostPayload

pytestmark = pytest.mark.unit


def make_response(status: int, data: object) -> Response:
    response = Response()
    response.status_code = status
    response._content = json.dumps(data).encode()
    response.headers["Content-Type"] = "application/json"
    response.url = "https://example.com/posts"
    response.request = Request("GET", response.url).prepare()
    return response


@pytest.mark.parametrize("invalid_id", ["1", True, 1.5])
def test_response_model_does_not_coerce_invalid_types(invalid_id) -> None:
    with pytest.raises(ValidationError):
        Post.model_validate({"id": invalid_id, "userId": 1, "title": "Title", "body": "Body"})


def test_response_model_requires_api_field_names() -> None:
    with pytest.raises(ValidationError):
        Post.model_validate({"id": 1, "user_id": 1, "title": "Title", "body": "Body"})


def test_request_dto_serializes_api_field_names() -> None:
    payload = PostPayload(user_id=1, title="Title", body="Body")

    assert payload.model_dump(by_alias=True) == {"userId": 1, "title": "Title", "body": "Body"}


def test_schema_error_is_reported_as_readable_assertion() -> None:
    with pytest.raises(AssertionError, match="Invalid Post schema"):
        assert_model(make_response(200, {"id": 1}), Post)


def test_status_error_shows_request_and_response() -> None:
    with pytest.raises(AssertionError) as error:
        assert_status(make_response(404, {}), 200)

    assert "Expected HTTP 200" in str(error.value)
    assert "GET https://example.com/posts" in str(error.value)
    assert "HTTP 404" in str(error.value)
