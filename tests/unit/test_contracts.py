import json

import pytest
from pydantic import ValidationError
from requests import Request, Response

from api_testing.assertions import assert_fields, assert_model
from api_testing.models import Comment, Company, Post, PostPayload
from tests.api.payload_validation import KnownPayloadValidationGap, assert_invalid_payload_rejected

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


@pytest.mark.parametrize(
    ("model", "payload", "api_name", "python_name"),
    [
        pytest.param(
            Post,
            {"id": 1, "userId": 1, "title": "Title", "body": "Body"},
            "userId",
            "user_id",
            id="post-user-id",
        ),
        pytest.param(
            Comment,
            {"id": 1, "postId": 1, "name": "Name", "email": "a@example.com", "body": "Body"},
            "postId",
            "post_id",
            id="comment-post-id",
        ),
        pytest.param(
            Company,
            {"name": "Company", "catchPhrase": "Phrase", "bs": "Business"},
            "catchPhrase",
            "catch_phrase",
            id="company-catch-phrase",
        ),
    ],
)
def test_response_models_require_api_field_names(model, payload, api_name, python_name) -> None:
    parsed = model.model_validate(payload)
    assert getattr(parsed, python_name) == payload[api_name]

    invalid_payload = {**payload, python_name: payload[api_name]}
    del invalid_payload[api_name]
    with pytest.raises(ValidationError) as error:
        model.model_validate(invalid_payload)

    assert any(
        detail["loc"] == (api_name,) and detail["type"] == "missing"
        for detail in error.value.errors()
    )


def test_request_dto_accepts_python_names_and_serializes_api_names() -> None:
    payload = PostPayload(user_id=1, title="Title", body="Body")

    assert payload.model_dump(by_alias=True) == {"userId": 1, "title": "Title", "body": "Body"}


def test_response_model_allows_additional_api_fields() -> None:
    post = Post.model_validate(
        {"id": 1, "userId": 1, "title": "Title", "body": "Body", "newField": "value"}
    )

    assert post.id == 1
    assert post.user_id == 1


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
