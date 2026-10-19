# JSONPlaceholder API tests

Automated API tests for the Users, Posts and Comments endpoints of
[JSONPlaceholder](https://jsonplaceholder.typicode.com/guide/).

Stack: Python 3.11+, pytest, requests, Pydantic, pytest-html.

## Quick start

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest
Start-Process .\reports\report.html
```

Linux / macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest
```

The HTML report is written to `reports/report.html`, the log to `reports/test-run.log`.

## Expected result

```text
57 passed, 13 xfailed
```

The 13 `xfailed` tests are **expected failures**, not a setup problem. They check that the
API rejects invalid input, but JSONPlaceholder is a demo service without validation:

- **JP-001** (12 tests): invalid payloads are accepted with HTTP 201 instead of 400/422.
- **JP-004** (1 test): malformed JSON returns HTTP 500 instead of 400.

Details and reproduction steps: [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md).
The markers are `strict`: if the API starts validating input, the run fails as a reminder
to remove them.

## Test scopes

| Command | What runs |
| --- | --- |
| `pytest` | Everything (70 tests) |
| `pytest -m smoke` | 6 quick checks of the main endpoints |
| `pytest -m full` | All 45 API tests |
| `pytest -m negative` | Missing resources and invalid input |
| `pytest -m unit` | 25 offline tests of the framework itself (no internet needed) |
| `pytest -m users` / `posts` / `comments` | One resource |
| `pytest -m "full and not contract"` | API tests without the known failures |

## Configuration

| CLI option | Environment variable | Default |
| --- | --- | --- |
| `--base-url` | `API_BASE_URL` | `https://jsonplaceholder.typicode.com` |
| `--connect-timeout` | `API_CONNECT_TIMEOUT` | 3.05 s |
| `--read-timeout` | `API_READ_TIMEOUT` | 10 s |
| `--retries` | `API_RETRIES` | 2 |

CLI options override environment variables. Example:

```bash
pytest -m smoke --base-url=https://jsonplaceholder.typicode.com --retries=1
```

Only GET requests are retried, and only on temporary server errors (429, 5xx).

## Project structure

```text
src/api_testing/
    config.py       Settings from CLI / environment
    client.py       HTTP session: timeouts, retries, logging
    api.py          UsersApi, PostsApi, CommentsApi — one method per endpoint
    models.py       Pydantic models for requests and responses
    assertions.py   Reusable checks: status, JSON, schema
tests/
    conftest.py     Fixtures and CLI options
    api/            API tests
    unit/           Offline tests of the client, config and models
docs/KNOWN_LIMITATIONS.md
```

A test calls an API method, gets a raw `requests.Response` and checks it with helpers
from `assertions.py`. API methods contain no assertions, so negative tests can inspect
4xx/5xx responses. On failure, the message shows the request, HTTP status and a
pretty-printed response body.

## Requirement coverage

| # | Scenario | Test |
| --- | --- | --- |
| 1 | `GET /users` | `test_get_users` |
| 2 | `GET /users/{id}` | `test_get_user_by_id` |
| 3 | `GET /users/9999` | `test_get_nonexistent_user` |
| 4 | `GET /posts` | `test_get_posts` |
| 5 | `POST /posts` | `test_create_post` |
| 6 | `PUT /posts/{id}` | `test_update_post` |
| 7 | `PATCH /posts/{id}` | `test_patch_post_preserves_other_fields` |
| 8 | `DELETE /posts/{id}` | `test_delete_post` |
| 9 | `GET /posts/{id}/comments` | `test_get_comments_for_post` |
| 10 | Invalid payload | `test_invalid_post_payload_is_rejected`, `test_malformed_json_is_rejected` |

Extra coverage: filtering posts by user, Unicode / long / special-character content,
invalid user IDs, a missing post, comments of a missing post.

## Adding a test

1. Add an endpoint method to `api.py` (or a new class based on `Resource`) and a model to
   `models.py` if needed.
2. Add a fixture in `tests/conftest.py` for a new resource.
3. Write the test in `tests/api/`, mark it `full` (and `smoke` if it is a key check).
   A one-line docstring becomes the test description in the HTML report.

## CI

GitHub Actions runs lint (`ruff`), offline tests and the full API suite on Python 3.11
and 3.12 for every push and pull request. Reports are kept as build artifacts for 14 days.
