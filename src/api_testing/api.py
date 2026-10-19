"""Resource API layer. Return raw responses and keep assertions in the test layer."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from requests import Response

from api_testing.client import ApiClient

Payload = BaseModel | dict[str, Any] | None


def serialize(payload: Payload) -> dict[str, Any] | None:
    # Raw dictionaries and None deliberately bypass DTO validation for negative tests.
    if isinstance(payload, BaseModel):
        return payload.model_dump(by_alias=True, exclude_unset=True)
    return payload


class Resource:
    """Base for resource clients: a new resource only declares its endpoints."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client


class UsersApi(Resource):
    def list(self) -> Response:
        return self.client.request("GET", "/users")

    def get(self, user_id: int | str) -> Response:
        return self.client.request("GET", f"/users/{user_id}")


class PostsApi(Resource):
    def list(self, *, user_id: int | None = None) -> Response:
        params = {"userId": user_id} if user_id is not None else None
        return self.client.request("GET", "/posts", params=params)

    def get(self, post_id: int) -> Response:
        return self.client.request("GET", f"/posts/{post_id}")

    def create(self, payload: Payload = None) -> Response:
        return self.client.request("POST", "/posts", json=serialize(payload))

    def create_raw(self, body: str | bytes) -> Response:
        """Send a JSON request body without encoding it, including malformed JSON."""
        return self.client.request("POST", "/posts", data=body)

    def update(self, post_id: int, payload: Payload) -> Response:
        return self.client.request("PUT", f"/posts/{post_id}", json=serialize(payload))

    def patch(self, post_id: int, payload: Payload) -> Response:
        return self.client.request("PATCH", f"/posts/{post_id}", json=serialize(payload))

    def delete(self, post_id: int) -> Response:
        return self.client.request("DELETE", f"/posts/{post_id}")


class CommentsApi(Resource):
    def for_post(self, post_id: int) -> Response:
        return self.client.request("GET", f"/posts/{post_id}/comments")
