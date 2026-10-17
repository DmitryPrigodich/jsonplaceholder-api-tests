"""Validated configuration; CLI values take precedence over environment variables."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    base_url: str = "https://jsonplaceholder.typicode.com"
    connect_timeout: float = Field(default=3.05, gt=0)
    read_timeout: float = Field(default=10.0, gt=0)
    retries: int = Field(default=2, ge=0, le=5)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("base URL must be an absolute http(s) URL")
        # Accessing port also detects malformed ports early.
        _ = parsed.port
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("base URL must not contain credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("base URL must not contain a query or fragment")
        return value

    @property
    def timeout(self) -> tuple[float, float]:
        return self.connect_timeout, self.read_timeout

    @classmethod
    def load(cls, **overrides: Any) -> Settings:
        env_names = {
            "base_url": "API_BASE_URL",
            "connect_timeout": "API_CONNECT_TIMEOUT",
            "read_timeout": "API_READ_TIMEOUT",
            "retries": "API_RETRIES",
        }
        values = {field: os.environ[env] for field, env in env_names.items() if env in os.environ}
        values.update({key: value for key, value in overrides.items() if value is not None})
        return cls.model_validate(values)
