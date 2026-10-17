"""HTTP transport: connection reuse, timeouts, bounded retries and request logging."""

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
        retry = Retry(
            total=settings.retries,
            connect=settings.retries,
            read=settings.retries,
            status=settings.retries,
            other=0,
            allowed_methods=frozenset({"GET", "HEAD", "OPTIONS"}),
            status_forcelist=(429, 500, 502, 503, 504),
            backoff_factor=0.3,
            backoff_max=3,
            # Keep execution bounded even if a public API sends a long Retry-After.
            respect_retry_after_header=False,
            raise_on_status=False,
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        # Only relative resource paths are accepted; the configured host stays authoritative.
        if "://" in path or path.startswith("//") or ".." in path.split("/"):
            raise ValueError("path must be a relative API resource path")
        url = f"{self.settings.base_url}/{path.lstrip('/')}"
        method = method.upper()
        kwargs.setdefault("timeout", self.settings.timeout)
        # An unexpected redirect is an API response to inspect, not another request to follow.
        kwargs.setdefault("allow_redirects", False)
        started = perf_counter()
        logger.info("Request %s %s", method, url)
        try:
            response = self.session.request(method, url, **kwargs)
        except requests.RequestException:
            logger.exception("Transport failure: %s %s", method, url)
            raise
        logger.info(
            "Response %s %s -> %s in %.3fs (retries=%d)",
            method,
            url,
            response.status_code,
            perf_counter() - started,
            len(response.raw.retries.history) if response.raw and response.raw.retries else 0,
        )
        # Do not raise_for_status here: negative tests need to inspect 4xx/5xx responses.
        return response

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
