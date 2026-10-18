import pytest

from api_testing.api import UsersApi
from api_testing.assertions import assert_json, assert_model, assert_model_list, assert_status
from api_testing.models import User

pytestmark = pytest.mark.full


@pytest.mark.smoke
def test_get_users(users_api: UsersApi) -> None:
    response = users_api.list()

    assert_status(response, 200)
    users = assert_model_list(response, User)
    assert users, "The users collection must not be empty"
    ids = [user.id for user in users]
    assert len(ids) == len(set(ids)), f"Duplicate user IDs: {ids}"


@pytest.mark.parametrize("user_id", [1, 5, 10])
def test_get_user_by_id(users_api: UsersApi, user_id: int) -> None:
    response = users_api.get(user_id)

    assert_status(response, 200)
    user = assert_model(response, User)
    assert user.id == user_id


@pytest.mark.negative
@pytest.mark.parametrize("user_id", [pytest.param(9999, marks=pytest.mark.smoke), 0, -1])
def test_get_nonexistent_user(users_api: UsersApi, user_id: int) -> None:
    response = users_api.get(user_id)

    assert_status(response, 404)
    assert assert_json(response) == {}
