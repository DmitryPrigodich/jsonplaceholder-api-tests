import json

import pytest
import requests

from api_testing.api import PostsApi
from api_testing.client import ApiClient
from api_testing.config import Settings
from api_testing.models import PostPayload

pytestmark = pytest.mark.unit


def test_get_retries_transient_http_errors(local_server) -> None:
    local_server.statuses = [503, 502, 200]
    with ApiClient(Settings(base_url=local_server.url, retries=2)) as client:
        response = client.request("GET", "/posts")

    assert response.status_code == 200
    assert len(local_server.requests) == 3


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_writes_are_not_retried_on_http_errors(local_server, method: str) -> None:
    local_server.statuses = [503, 200]
    with ApiClient(Settings(base_url=local_server.url, retries=2)) as client:
        response = client.request(method, "/posts/1", json={"title": "example"})

    assert response.status_code == 503
    assert len(local_server.requests) == 1


def test_client_error_is_not_retried(local_server) -> None:
    local_server.statuses = [400, 200]
    with ApiClient(Settings(base_url=local_server.url, retries=2)) as client:
        response = client.request("GET", "/posts")

    assert response.status_code == 400
    assert len(local_server.requests) == 1


def test_exhausted_status_retries_return_last_response(local_server) -> None:
    local_server.statuses = [503]
    with ApiClient(Settings(base_url=local_server.url, retries=1)) as client:
        response = client.request("GET", "/posts")

    assert response.status_code == 503
    assert len(local_server.requests) == 2


def test_read_timeout_is_enforced(local_server) -> None:
    local_server.delay = 0.2
    with ApiClient(Settings(base_url=local_server.url, read_timeout=0.02, retries=0)) as client:
        # A write is deliberately used: no read retry can wrap the original Timeout.
        with pytest.raises(requests.Timeout):
            client.request("POST", "/posts", json={"title": "slow response"})

    assert len(local_server.requests) == 1


def test_base_url_path_prefix_is_preserved(local_server) -> None:
    with ApiClient(Settings(base_url=f"{local_server.url}/api/v1/")) as client:
        client.request("GET", "/posts")

    assert local_server.requests[0]["path"] == "/api/v1/posts"


def test_payload_dto_raw_invalid_data_and_absent_body_reach_server(local_server) -> None:
    payload = PostPayload(user_id=1, title="Title", body="Body")
    with ApiClient(Settings(base_url=local_server.url)) as client:
        posts = PostsApi(client)
        posts.create(payload)
        posts.create({"userId": "wrong", "title": False})
        posts.create()

    assert json.loads(local_server.requests[0]["body"]) == {
        "userId": 1,
        "title": "Title",
        "body": "Body",
    }
    assert json.loads(local_server.requests[1]["body"]) == {"userId": "wrong", "title": False}
    assert local_server.requests[2]["body"] == b""
