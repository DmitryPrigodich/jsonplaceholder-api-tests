"""Reusable HTTP, JSON and schema assertions with useful failure diagnostics."""

from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from requests import Response

Model = TypeVar("Model", bound=BaseModel)

MAX_BODY_CHARS = 1000


def format_body(response: Response) -> str:
    """Pretty-print JSON so a failure can be read without pasting it into a formatter."""
    try:
        text = json.dumps(response.json(), indent=2, ensure_ascii=False)
    except ValueError:
        text = response.text
    if len(text) > MAX_BODY_CHARS:
        text = f"{text[:MAX_BODY_CHARS]}\n... ({len(text) - MAX_BODY_CHARS} more characters)"
    return text or "<empty body>"


def response_details(response: Response) -> str:
    return (
        f"\nRequest:  {response.request.method} {response.url}\n"
        f"Response: HTTP {response.status_code}\n"
        f"Body:\n{format_body(response)}"
    )


def assert_status(response: Response, expected: int | tuple[int, ...]) -> None:
    statuses = (expected,) if isinstance(expected, int) else expected
    assert response.status_code in statuses, (
        f"Expected HTTP {' or '.join(map(str, statuses))}; {response_details(response)}"
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
