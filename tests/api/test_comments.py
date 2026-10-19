import pytest

from api_testing.api import CommentsApi
from api_testing.assertions import assert_json, assert_model_list, assert_status
from api_testing.models import Comment

pytestmark = [pytest.mark.full, pytest.mark.comments]


@pytest.mark.parametrize("post_id", [pytest.param(1, marks=pytest.mark.smoke), 50, 100])
def test_get_comments_for_post(comments_api: CommentsApi, post_id: int) -> None:
    """Comments of a post belong to that post and have unique IDs."""

    response = comments_api.for_post(post_id)

    assert_status(response, 200)
    comments = assert_model_list(response, Comment)
    assert comments, f"Expected comments for post {post_id}"
    assert all(comment.post_id == post_id for comment in comments)
    ids = [comment.id for comment in comments]
    assert len(ids) == len(set(ids)), f"Duplicate comment IDs: {ids}"


@pytest.mark.negative
def test_comments_for_nonexistent_post_are_empty(comments_api: CommentsApi) -> None:
    """A missing post has an empty comment list."""

    response = comments_api.for_post(9999)

    assert_status(response, 200)
    assert assert_json(response) == []
