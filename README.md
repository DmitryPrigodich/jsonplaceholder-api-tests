# JSONPlaceholder API tests

Automated tests for Users, Posts and Comments in the public
[JSONPlaceholder API](https://jsonplaceholder.typicode.com/guide/).
Built with Python 3.11+, pytest, requests and Pydantic, with standalone pytest-html reports.
HTTP transport, resource methods, response validation and test scenarios have separate responsibilities.

The [assignment brief](#assignment-brief) below is an English translation of the original task.

## Quick start

Run commands from the project root. Python 3.11+ and internet access are required;
no account or API key is needed.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest
Start-Process .\reports\report.html
```

Activation is optional because these commands use the environment's interpreter directly.
If `py` is unavailable, use `python -m venv .venv` with Python 3.11+.

### Linux and macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest
```

Open `reports/report.html` in a browser. It is a standalone file; no report server or Java is needed.

## Select a test scope

Below, `python` means the interpreter in `.venv`. Without activation, substitute
`.\.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on Linux/macOS.

| Command | Scope |
| --- | --- |
| `python -m pytest` | All API and offline component tests |
| `python -m pytest -m smoke` | Six checks: users, posts, create, update, comments and a missing user |
| `python -m pytest -m full` | All API tests, including negative scenarios |
| `python -m pytest -m negative` | Missing resources and invalid payloads |
| `python -m pytest -m unit` | Offline component tests, including a local HTTP server |
| `python -m pytest -m "full and not contract"` | API tests excluding the assumed validation contract |
| `python -m pytest -m contract --runxfail` | Show deviations from the assumed contract as ordinary failures |
| `python -m pytest --collect-only -q` | List tests without sending requests |

`smoke` is a subset of `full`. Only one parameter of each selected scenario is marked smoke;
the other parameters still run in full. Markers are registered and `--strict-markers`
rejects unknown markers attached to tests.

## Interpreting results

Verified locally on Windows with Python 3.12.6 on October 19, 2026:

| Scope | Result |
| --- | --- |
| API (`full`) | 24 passed, 12 xfailed |
| Components (`unit`) | 45 passed |
| Total | 81 tests: 69 passed, 12 xfailed |

The negative payload tests assume that missing fields, wrong types, empty strings and
nonpositive user IDs should be rejected with HTTP 400/422. **This is an explicit assumption
for the assignment, not a documented JSONPlaceholder validation guarantee.**

JSONPlaceholder accepts these requests with HTTP 201. Twelve cases therefore use a narrow,
strict `xfail`: only the verified acceptance-and-echo response is an expected failure.
Network errors, HTTP 5xx and unexpected response bodies still fail normally. If the server
starts rejecting a payload, `XPASS(strict)` fails the run so the expectation can be reviewed.
See [known limitations](docs/KNOWN_LIMITATIONS.md) for the exact cases and reproduction steps.

Writes are simulated and are not persisted. Tests inspect each operation's response;
they do not attempt to retrieve a newly created post or expect a deleted post to disappear.
Results also depend on the availability of the public service.

## Requirement coverage

| Scenario | Test |
| --- | --- |
| `GET /users` | `test_get_users` |
| `GET /users/{id}` | `test_get_user_by_id`, IDs 1, 5, 10 |
| `GET /users/9999` | `test_get_nonexistent_user`, also IDs 0 and -1 |
| `GET /posts` | `test_get_posts` |
| `POST /posts` | `test_create_post` |
| `PUT /posts/{id}` | `test_update_post`, IDs 1, 50, 100 |
| `PATCH /posts/{id}` | `test_patch_post_preserves_other_fields` |
| `DELETE /posts/{id}` | `test_delete_post` |
| `GET /posts/{id}/comments` | `test_get_comments_for_post`, IDs 1, 50, 100 |
| Missing required fields | `test_invalid_post_payload_is_rejected`, one case per field |
| Wrong field types | The same test, one invalid field per case |
| Empty strings and nonpositive user IDs | The same test, separate boundary cases |
| Empty JSON and no request body | The same test, `empty-object` / `empty-request-body` |

Additional checks cover filtering posts by user, a missing post, an empty comments collection
for a missing post, unique collection IDs and unchanged fields after PATCH.
Every returned list item is validated against its response model.

## Project structure

```text
src/api_testing/
    config.py       Settings, validation and environment overrides
    client.py       HTTP session, timeouts, retries and logging
    api.py          UsersApi, PostsApi and CommentsApi resource methods
    models.py       Request DTOs and strict response schemas
    assertions.py   Reusable HTTP, JSON, schema and field checks
tests/
    conftest.py     CLI options, fixtures and session cleanup
    api/
        test_*.py              API scenarios
        payload_validation.py  JSONPlaceholder-specific expected-failure classification
    unit/           Offline component checks
docs/
    KNOWN_LIMITATIONS.md
.github/workflows/tests.yml
```

A test calls a resource method, receives a `requests.Response`, checks the status and schema,
then checks scenario-specific values. API methods contain no assertions and do not call
`raise_for_status()`, so tests can inspect error responses.

Request DTOs accept Python field names such as `user_id` and serialize them as `userId`.
Response models require API field names: `user_id` cannot replace `userId` in a server response.
Types are strict (`"1"` and `true` are not integer IDs), while additional response fields are allowed.
Raw dictionaries and `None` bypass DTO validation for negative requests.

The HTTP session and resource objects are shared for one test run and closed during teardown.
Payload fixtures create a fresh DTO for each test. Tests are independent of execution order.

## Configuration

Precedence: **CLI options > environment variables > defaults**.

| CLI option | Environment variable | Default |
| --- | --- | --- |
| `--base-url` | `API_BASE_URL` | `https://jsonplaceholder.typicode.com` |
| `--connect-timeout` | `API_CONNECT_TIMEOUT` | 3.05 seconds |
| `--read-timeout` | `API_READ_TIMEOUT` | 10 seconds |
| `--retries` | `API_RETRIES` | 2 retries |

```bash
python -m pytest -m smoke --base-url=https://jsonplaceholder.typicode.com --read-timeout=15 --retries=1
```

Environment overrides in PowerShell:

```powershell
$env:API_BASE_URL = "https://jsonplaceholder.typicode.com"
$env:API_READ_TIMEOUT = "15"
.\.venv\Scripts\python.exe -m pytest -m smoke
```

Base URLs may include a path prefix, such as `https://host.example/api/v1`.
Invalid URLs, nonpositive or nonfinite timeouts, and retry counts outside 0..5 are rejected
before tests run. `.env` files are not loaded automatically. Another base URL must provide
compatible routes and test data.

Retries apply to the HTTP transport, not failed assertions. GET/HEAD/OPTIONS may be retried
after HTTP 429/500/502/503/504 or eligible read errors. Writes are not retried after an HTTP
error or read error; connection failures before sending a request may be retried for any method.
The retry budget is shared: `--retries=2` means at most three attempts. Backoff uses a factor
of 0.3 and a three-second cap; `Retry-After` is disabled to avoid excessive server-directed waits.
The final error response or network exception reaches the test. Redirects are not followed.
Connect/read timeouts limit individual I/O stages, not the total duration including retries.

## Reports and logs

A normal run writes `reports/report.html` and `reports/test-run.log`.
The log includes method, URL, status, elapsed time and retry count; request bodies and
authorization headers are not logged. Assertion failures include response diagnostics.

Use separate paths to keep artifacts from multiple runs:

```bash
python -m pytest -m full --html=reports/api.html --log-file=reports/api.log --junitxml=reports/junit.xml
```

Reports, logs, environments and caches are ignored by Git. Reusing a report or log path
overwrites the previous file.

## Quality checks and CI

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -m unit
```

GitHub Actions runs on push, pull request and manual dispatch for Python 3.11 and 3.12.
It installs pinned dependencies, checks lint and formatting, then runs offline and full API tests.
HTML reports and logs from both scopes, plus JUnit results from the API suite, are retained
for 14 days, including failed runs. The workflow has read-only repository permissions and needs no secrets.
[Earlier CI baseline and artifacts](https://github.com/DmitryPrigodich/jsonplaceholder-api-tests/actions/runs/39070870099)
cover the version before the latest review changes.

## Adding a scenario

1. Add a resource method in `api.py` and a model in `models.py` if needed.
2. Reuse a fixture or introduce one for a new resource.
3. Add a test under `tests/api/` with `full`; mark representative quick checks with `smoke`.
4. Parametrize similar cases. Keep reusable protocol checks in `assertions.py` and
   scenario-specific expectations with the tests.
5. Run the affected tests and quality checks.

## Assignment brief

### API test automation assignment for a QA Engineer position

Develop an automated API testing system using Python. You may use Python frameworks of your choice.

Test environment: https://jsonplaceholder.typicode.com/guide/

### Technical requirements

- Python 3.11+
- pytest
- requests / httpx
- pytest markers
- Configurable base URL
- Logging
- HTML / Allure reporting

### Architectural requirements

The system must:

- Support growth of the test suite.
- Separate the API layer, assertions and test logic.
- Avoid duplication.
- Use reusable components.

### Desirable features

- API client abstraction
- Models / DTOs
- Fixtures
- Parametrization
- Negative scenarios
- Retries / timeout handling
- Schema validation (optional)

A README is required.

### Minimum required coverage

Implement automated API tests for at least the following scenarios.

#### Users

1. Retrieve the list of users: `GET /users`.
2. Retrieve a specific user by ID: `GET /users/{id}`.
3. Check the response when requesting a nonexistent user: `GET /users/9999`.

#### Posts

4. Retrieve the list of posts: `GET /posts`.
5. Create a new post: `POST /posts`.
6. Update a post: `PUT /posts/{id}`.
7. Partially update a post: `PATCH /posts/{id}`.
8. Delete a post: `DELETE /posts/{id}`.

#### Comments

9. Retrieve comments for a specific post: `GET /posts/{id}/comments`.

#### Negative scenarios

10. Check the handling of an invalid payload, for example:
    - Missing required fields.
    - Incorrect data types.
    - An empty request body.

Tests must be divided into scopes (`@smoke`, `@full`, etc.). It must be possible to run
tests by selecting a specific scope.
