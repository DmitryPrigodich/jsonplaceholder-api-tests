"""HTTP client: one shared session with timeouts, retries and request logging."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from api_testing.config import Settings

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )
        # Only safe GET-like requests are retried, and only on temporary server errors.
        retry = Retry(
            total=settings.retries,
            allowed_methods=frozenset({"GET", "HEAD", "OPTIONS"}),
            status_forcelist=(429, 500, 502, 503, 504),
            backoff_factor=0.3,
            raise_on_status=False,
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.settings.base_url}/{path.lstrip('/')}"
        kwargs.setdefault("timeout", self.settings.timeout)
        started = perf_counter()
        logger.info("Request %s %s", method, url)
        response = self.session.request(method, url, **kwargs)
        logger.info(
            "Response %s %s -> %s in %.3fs",
            method,
            url,
            response.status_code,
            perf_counter() - started,
        )
        # No raise_for_status(): negative tests need to inspect 4xx/5xx responses.
        return response

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
