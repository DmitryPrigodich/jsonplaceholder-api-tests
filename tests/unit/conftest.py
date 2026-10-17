"""A local HTTP server verifies real requests/urllib3 behavior without the public API."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from time import sleep
from typing import Any

import pytest


@dataclass
class LocalServer:
    url: str = ""
    statuses: list[int] = field(default_factory=lambda: [200])
    delay: float = 0
    requests: list[dict[str, Any]] = field(default_factory=list)


@pytest.fixture
def local_server() -> Iterator[LocalServer]:
    state = LocalServer()

    class Handler(BaseHTTPRequestHandler):
        def handle_request(self) -> None:
            state.requests.append(
                {
                    "method": self.command,
                    "path": self.path,
                    "body": self.rfile.read(int(self.headers.get("Content-Length", 0))),
                    "headers": dict(self.headers),
                }
            )
            status = state.statuses[0]
            if len(state.statuses) > 1:
                state.statuses.pop(0)
            sleep(state.delay)
            body = b'{"ok": true}'
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                # A timeout test deliberately disconnects before the server writes its body.
                pass

        do_GET = handle_request
        do_POST = handle_request
        do_PUT = handle_request
        do_PATCH = handle_request
        do_DELETE = handle_request

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state.url = f"http://127.0.0.1:{server.server_port}"
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
