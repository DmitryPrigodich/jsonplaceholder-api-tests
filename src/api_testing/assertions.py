"""Reusable HTTP, JSON and schema assertions with useful failure diagnostics."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from requests import Response

Model = TypeVar("Model", bound=BaseModel)


def response_details(response: Response) -> str:
    return (
        f"{response.request.method} {response.url}\n"
        f"status={response.status_code}, body={response.text[:1000]!r}"
    )


def assert_status(response: Response, expected: int | tuple[int, ...]) -> None:
    statuses = (expected,) if isinstance(expected, int) else expected
    assert response.status_code in statuses, (
        f"Expected HTTP {statuses}; {response_details(response)}"
    )


def assert_json(response: Response) -> Any:
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    assert content_type == "application/json", (
        f"Expected application/json, got {content_type!r}; {response_details(response)}"
    )
    try:
        return response.json()
    except ValueError as exc:
        raise AssertionError(f"Invalid JSON; {response_details(response)}") from exc


def assert_model(response: Response, model: type[Model]) -> Model:
    data = assert_json(response)
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise AssertionError(f"Invalid {model.__name__} schema: {exc}") from exc


def assert_model_list(response: Response, model: type[Model]) -> list[Model]:
    data = assert_json(response)
    assert isinstance(data, list), f"Expected a JSON array; {response_details(response)}"
    result = []
    for index, item in enumerate(data):
        try:
            result.append(model.model_validate(item))
        except ValidationError as exc:
            raise AssertionError(f"Invalid {model.__name__} at index {index}: {exc}") from exc
    return result


def assert_fields(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    assert isinstance(actual, dict), f"Expected JSON object, got {type(actual).__name__}"
    for key, value in expected.items():
        assert key in actual, f"Missing field {key!r}: {actual!r}"
        assert type(actual[key]) is type(value) and actual[key] == value, (
            f"Field {key!r}: expected {value!r} ({type(value).__name__}), "
            f"got {actual[key]!r} ({type(actual[key]).__name__})"
        )


class KnownPayloadValidationGap(AssertionError):
    """Only the verified JSONPlaceholder validation gap is an expected failure."""


def assert_invalid_payload_rejected(response: Response, payload: dict[str, Any] | None) -> None:
    if response.status_code == 201:
        # Verify the precise known behavior before classifying it as a known limitation.
        # Transport errors, 5xx, HTML, malformed JSON and unexpected bodies must fail normally.
        data = assert_json(response)
        expected = payload or {}
        assert_fields(data, expected)
        assert set(data) == set(expected) | {"id"}, f"Unexpected response fields: {data!r}"
        assert type(data["id"]) is int and data["id"] > 0, f"Invalid generated ID: {data!r}"
        raise KnownPayloadValidationGap(
            "Invalid payload was accepted and echoed with HTTP 201; expected HTTP 400 or 422. "
            f"Payload: {payload!r}. {response_details(response)}"
        )
    assert_status(response, (400, 422))
