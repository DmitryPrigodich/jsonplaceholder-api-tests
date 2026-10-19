import pytest

from api_testing.api import PostsApi
from api_testing.assertions import (
    assert_json,
    assert_model,
    assert_model_list,
    assert_status,
)
from api_testing.models import Post, PostPayload

pytestmark = [pytest.mark.full, pytest.mark.posts]


@pytest.mark.smoke
def test_get_posts(posts_api: PostsApi) -> None:
    """The post list is returned, matches the schema and has unique IDs."""

    response = posts_api.list()

    assert_status(response, 200)
    posts = assert_model_list(response, Post)
    assert posts, "The posts collection must not be empty"
    ids = [post.id for post in posts]
    assert len(ids) == len(set(ids)), f"Duplicate post IDs: {ids}"


@pytest.mark.parametrize("user_id", [1, 5, 10])
def test_filter_posts_by_user(posts_api: PostsApi, user_id: int) -> None:
    """Filtering by userId returns only that user's posts."""

    response = posts_api.list(user_id=user_id)

    assert_status(response, 200)
    posts = assert_model_list(response, Post)
    assert posts, f"Expected posts for user {user_id}"
    assert all(post.user_id == user_id for post in posts)


@pytest.mark.parametrize(
    ("title", "body"),
    [
        pytest.param("Test title", "Test body", id="basic", marks=pytest.mark.smoke),
        pytest.param("Café 🚀", "Résumé — こんにちは 🌍", id="unicode"),
        pytest.param("x" * 500, "y" * 2000, id="long-text"),
        pytest.param('<b>spec</b> & "quotes"', "line1\nline2\tend\\path", id="special-characters"),
    ],
)
def test_create_post(posts_api: PostsApi, title: str, body: str) -> None:
    """A new post is created and the response echoes the submitted fields."""

    post_payload = PostPayload(user_id=1, title=title, body=body)

    response = posts_api.create(post_payload)

    assert_status(response, 201)
    post = assert_model(response, Post)
    assert post.user_id == post_payload.user_id
    assert post.title == post_payload.title
    assert post.body == post_payload.body


@pytest.mark.parametrize("post_id", [pytest.param(1, marks=pytest.mark.smoke), 50, 100])
def test_update_post(posts_api: PostsApi, post_payload: PostPayload, post_id: int) -> None:
    """PUT replaces a post and the response contains the submitted fields."""

    response = posts_api.update(post_id, post_payload)

    assert_status(response, 200)
    post = assert_model(response, Post)
    assert post.id == post_id
    assert post.user_id == post_payload.user_id
    assert post.title == post_payload.title
    assert post.body == post_payload.body


@pytest.mark.parametrize("post_id", [1, 100])
@pytest.mark.parametrize(
    "patch",
    [
        pytest.param({"title": "Updated title only"}, id="title"),
        pytest.param({"body": "Updated body only"}, id="body"),
        pytest.param({"userId": 7}, id="user-id"),
    ],
)
def test_patch_post_preserves_other_fields(
    posts_api: PostsApi, post_id: int, patch: dict[str, str | int]
) -> None:
    """PATCH changes only the submitted field and keeps the rest."""

    original_response = posts_api.get(post_id)
    assert_status(original_response, 200)
    original = assert_model(original_response, Post)

    response = posts_api.patch(post_id, patch)

    assert_status(response, 200)
    post = assert_model(response, Post)
    expected = original.model_dump(by_alias=True) | patch
    assert post.model_dump(by_alias=True) == expected


@pytest.mark.parametrize("post_id", [1, 100])
def test_delete_post(posts_api: PostsApi, post_id: int) -> None:
    """Deleting a post returns HTTP 200 with an empty object."""

    response = posts_api.delete(post_id)

    assert_status(response, 200)
    assert assert_json(response) == {}


@pytest.mark.negative
def test_get_nonexistent_post(posts_api: PostsApi) -> None:
    """A missing post returns HTTP 404 with an empty object."""

    response = posts_api.get(9999)

    assert_status(response, 404)
    assert assert_json(response) == {}
