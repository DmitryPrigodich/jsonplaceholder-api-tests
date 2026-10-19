import pytest
from pydantic import ValidationError

from api_testing.config import Settings

pytestmark = pytest.mark.unit


def test_cli_overrides_environment_and_environment_overrides_defaults(monkeypatch) -> None:
    monkeypatch.setenv("API_BASE_URL", "https://environment.example/api/")
    monkeypatch.setenv("API_READ_TIMEOUT", "4.5")
    monkeypatch.setenv("API_RETRIES", "1")

    settings = Settings.load(base_url="https://cli.example/v1/", retries=0)

    assert settings.base_url == "https://cli.example/v1"
    assert settings.read_timeout == 4.5
    assert settings.retries == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"base_url": "example.com"},
        {"base_url": "ftp://example.com"},
        {"connect_timeout": 0},
        {"read_timeout": -1},
        {"retries": -1},
        {"retries": 6},
    ],
)
def test_invalid_configuration_is_rejected(overrides) -> None:
    with pytest.raises(ValidationError):
        Settings(**overrides)
