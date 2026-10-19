# JSONPlaceholder limitations

These characteristics of the public demo API affect how test results should be interpreted.
The expanded negative cases below were verified with real requests on October 19, 2026.

## JP-001: Invalid post payloads are accepted

For this assignment, the negative tests assume that creating a post requires nonempty
string `title` and `body` fields and a positive integer `userId`. Missing fields, incorrect
types and invalid boundary values are expected to produce HTTP 400/422.

**This is an assumed validation contract, not a documented guarantee of JSONPlaceholder.**
Acceptance of these inputs is a deviation from that assumption, not evidence that the
demo service violates its own specification.

In practice, `POST /posts` responds with HTTP 201 and adds an `id` to the supplied data:

| Case | Payload | Observed response |
| --- | --- | --- |
| Missing title | `{"body":"Body","userId":1}` | 201; title remains absent |
| Missing body | `{"title":"Title","userId":1}` | 201; body remains absent |
| Missing user ID | `{"title":"Title","body":"Body"}` | 201; userId remains absent |
| Wrong title type | `{"title":123,"body":"Body","userId":1}` | 201; numeric title is echoed |
| Wrong body type | `{"title":"Title","body":false,"userId":1}` | 201; boolean body is echoed |
| Wrong user ID type | `{"title":"Title","body":"Body","userId":"wrong"}` | 201; string userId is echoed |
| Empty title | `{"title":"","body":"Body","userId":1}` | 201; empty title is echoed |
| Empty body | `{"title":"Title","body":"","userId":1}` | 201; empty body is echoed |
| Zero user ID | `{"title":"Title","body":"Body","userId":0}` | 201; zero userId is echoed |
| Negative user ID | `{"title":"Title","body":"Body","userId":-1}` | 201; negative userId is echoed |
| Empty JSON object | `{}` | 201; only a generated id is returned |
| No request body | No bytes, with `Content-Type: application/json` | 201; only a generated id is returned |

Each field-specific case changes one field while keeping the others valid, so rejection
of one invalid field cannot be mistaken for validation of the others.

### Minimal reproduction

```http
POST /posts HTTP/1.1
Host: jsonplaceholder.typicode.com
Content-Type: application/json

{}
```

Observed response:

```http
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8

{"id":101}
```

### How tests classify the result

The twelve parameters of `test_invalid_post_payload_is_rejected` use
`xfail(strict=True, raises=KnownPayloadValidationGap)`.
The classification helper lives beside the API tests in
`tests/api/payload_validation.py`, rather than in the reusable assertion layer.

For HTTP 201, the helper verifies JSON content, unchanged input fields and types,
the exact response field set, and a positive integer ID. Only that precise response
raises `KnownPayloadValidationGap`.

- Verified acceptance and echo of invalid data produces `XFAIL`.
- Network failures, HTTP 5xx, HTML, malformed JSON and unexpected bodies produce `FAIL`/`ERROR`.
- HTTP 400/422 satisfies the assumed contract, producing `XPASS(strict)` and a failing run.
  Review the changed behavior and remove or narrow the marker as appropriate.

This avoids hiding arbitrary failures behind `xfail`. To display the deviations as ordinary failures:

```bash
python -m pytest -m contract -k invalid_post_payload --runxfail
```

On the current service, expect twelve failures and a nonzero exit code.
This command demonstrates the difference between observed behavior and the assignment's
assumed contract; it does not establish twelve bugs in JSONPlaceholder.

## JP-002: Writes are not persisted

Create, PUT, PATCH and DELETE simulate writes without changing persistent data.
This is documented in the [official guide](https://jsonplaceholder.typicode.com/guide/).

Tests check each write response independently instead of building a dependent
create/read/update/delete chain. They do not fetch a newly created ID or expect GET to return
404 after DELETE. Cleanup is unnecessary because the writes are not persisted.
The PATCH test reads an existing post first to check that other fields are preserved in the response.

For an API with persistent storage, the approach would need unique test data, read-back
verification and cleanup in a yield fixture or finalizer, including after test failures.

## JP-003: Public service and fixed test data

API tests require internet access and compatible data: users 1, 5 and 10; posts 1, 50 and 100;
and their comments. Collections are checked for schemas, relationships and unique IDs
without relying on exact post text or the precise size of every collection.

A missing user/post returns HTTP 404. The comments collection for a missing post returns
HTTP 200 with an empty array. These are distinct scenarios with separate tests.

Changing the base URL changes request destinations, not the API contract or data expectations.
Offline component tests (`-m unit`) do not contact the public service; transport tests use
a temporary local HTTP server.

## JP-004: Malformed JSON causes a server error

Unlike the valid JSON objects in JP-001, this request cannot be parsed as JSON at all:

```http
POST /posts HTTP/1.1
Host: jsonplaceholder.typicode.com
Content-Type: application/json

{not a json
```

The test expects HTTP 400 for a malformed request. The observed response is HTTP 500,
with a stack trace beginning with:

```text
SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)
    at JSON.parse (<anonymous>)
    at parse (/app/node_modules/body-parser/lib/types/json.js:89:19)
```

`test_malformed_json_is_rejected` sends the exact text through `PostsApi.create_raw()`.
The body is not JSON-encoded into a valid string, and the POST is not retried after HTTP 500.
An offline transport test verifies both behaviors.

The test uses `xfail(strict=True, raises=KnownMalformedJsonError)`. Only HTTP 500 with
the observed syntax-error prefix and both `JSON.parse` and `body-parser` stack entries
is classified as this known failure. Generic 500 responses, different parser failures,
other statuses and transport errors remain ordinary failures. Local tests verify that
the classification does not hide these unrelated problems.

HTTP 500 is not an accepted success status. It remains a documented server error.
If the service starts returning HTTP 400, `XPASS(strict)` requires the marker to be reviewed.

To demonstrate this failure without xfail handling:

```bash
python -m pytest -m contract -k malformed_json --runxfail
```

To demonstrate all known validation deviations, including JP-001:

```bash
python -m pytest -m contract --runxfail
```

The latter command currently produces thirteen failures and a nonzero exit code.
