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
