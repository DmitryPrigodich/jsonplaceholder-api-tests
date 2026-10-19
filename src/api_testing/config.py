"""Test run settings. Priority: CLI options > environment variables > defaults."""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    base_url: str = "https://jsonplaceholder.typicode.com"
    connect_timeout: float = Field(default=3.05, gt=0)
    read_timeout: float = Field(default=10.0, gt=0)
    retries: int = Field(default=2, ge=0, le=5)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("base URL must start with http:// or https://")
        return value.rstrip("/")

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
