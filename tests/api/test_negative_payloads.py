from typing import Any

import pytest

from api_testing.api import PostsApi
from tests.api.payload_validation import KnownPayloadValidationGap, assert_invalid_payload_rejected

pytestmark = [pytest.mark.full, pytest.mark.negative, pytest.mark.contract]

INVALID_PAYLOADS = [
    pytest.param({"body": "Body", "userId": 1}, id="missing-title"),
    pytest.param({"title": "Title", "userId": 1}, id="missing-body"),
    pytest.param({"title": "Title", "body": "Body"}, id="missing-user-id"),
    pytest.param({"title": 123, "body": "Body", "userId": 1}, id="wrong-title-type"),
    pytest.param({"title": "Title", "body": False, "userId": 1}, id="wrong-body-type"),
    pytest.param({"title": "Title", "body": "Body", "userId": "wrong"}, id="wrong-user-id-type"),
    pytest.param({"title": "", "body": "Body", "userId": 1}, id="empty-title"),
    pytest.param({"title": "Title", "body": "", "userId": 1}, id="empty-body"),
    pytest.param({"title": "Title", "body": "Body", "userId": 0}, id="zero-user-id"),
    pytest.param({"title": "Title", "body": "Body", "userId": -1}, id="negative-user-id"),
    pytest.param({}, id="empty-object"),
    pytest.param(None, id="empty-request-body"),
]


@pytest.mark.parametrize("payload", INVALID_PAYLOADS)
@pytest.mark.xfail(
    strict=True,
    raises=KnownPayloadValidationGap,
    reason="JSONPlaceholder accepts invalid post payloads; see docs/KNOWN_LIMITATIONS.md",
)
def test_invalid_post_payload_is_rejected(
    posts_api: PostsApi, payload: dict[str, Any] | None
) -> None:
    response = posts_api.create(payload)

    assert_invalid_payload_rejected(response, payload)
