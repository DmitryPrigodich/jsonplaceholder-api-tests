"""Shared test setup and pytest CLI configuration."""

from collections.abc import Iterator

import pytest
from pydantic import ValidationError

from api_testing.api import CommentsApi, PostsApi, UsersApi
from api_testing.client import ApiClient
from api_testing.config import Settings
from api_testing.models import PostPayload

SETTINGS = pytest.StashKey[Settings]()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("api", "API connection settings (CLI > environment > defaults)")
    group.addoption("--base-url", help="API base URL; env: API_BASE_URL")
    group.addoption("--connect-timeout", type=float, help="Seconds; env: API_CONNECT_TIMEOUT")
    group.addoption("--read-timeout", type=float, help="Seconds; env: API_READ_TIMEOUT")
    group.addoption("--retries", type=int, help="Retry budget, 0..5; env: API_RETRIES")


def pytest_configure(config: pytest.Config) -> None:
    try:
        config.stash[SETTINGS] = Settings.load(
            base_url=config.getoption("base_url"),
            connect_timeout=config.getoption("connect_timeout"),
            read_timeout=config.getoption("read_timeout"),
            retries=config.getoption("retries"),
        )
    except (ValidationError, ValueError) as exc:
        raise pytest.UsageError(f"Invalid API configuration: {exc}") from exc


def pytest_report_header(config: pytest.Config) -> str:
    settings = config.stash[SETTINGS]
    return (
        f"API: {settings.base_url}; connect/read timeout: {settings.timeout}s; "
        f"retries: {settings.retries}"
    )


@pytest.fixture(scope="session")
def settings(pytestconfig: pytest.Config) -> Settings:
    return pytestconfig.stash[SETTINGS]


@pytest.fixture(scope="session")
def api_client(settings: Settings) -> Iterator[ApiClient]:
    with ApiClient(settings) as client:
        yield client


@pytest.fixture(scope="session")
def users_api(api_client: ApiClient) -> UsersApi:
    return UsersApi(api_client)


@pytest.fixture(scope="session")
def posts_api(api_client: ApiClient) -> PostsApi:
    return PostsApi(api_client)


@pytest.fixture(scope="session")
def comments_api(api_client: ApiClient) -> CommentsApi:
    return CommentsApi(api_client)


@pytest.fixture
def post_payload() -> PostPayload:
    # A new DTO per test prevents mutable test data from leaking between cases.
    return PostPayload(user_id=1, title="API automation test", body="A reusable test payload.")
