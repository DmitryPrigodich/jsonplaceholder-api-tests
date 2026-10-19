# Known limitations of JSONPlaceholder

JSONPlaceholder is a public demo API. Some of its behavior differs from what a real API
would do, and the tests account for that.

## JP-001: Invalid post payloads are accepted

The negative tests assume that `POST /posts` requires a nonempty `title`, a nonempty `body`
and a positive integer `userId`, and that invalid input returns HTTP 400 or 422.
This is our assumption for the assignment; JSONPlaceholder does not promise validation.

In reality the service returns HTTP 201 and echoes back whatever was sent:

```http
POST /posts
Content-Type: application/json

{}
```

```http
HTTP/1.1 201 Created

{"id": 101}
```

The 12 cases of `test_invalid_post_payload_is_rejected` (missing fields, wrong types, empty
strings, zero/negative `userId`, empty object, empty body) are therefore marked
`xfail(strict=True)`. To see them as ordinary failures:

```bash
pytest -m contract --runxfail
```

## JP-002: Writes are not persisted

POST, PUT, PATCH and DELETE are simulated: the response looks real, but nothing is saved
([official guide](https://jsonplaceholder.typicode.com/guide/)). So tests check each write
response on its own and do not read the data back. With a real API, tests would also
read back the result and clean up the created data.

## JP-003: Public service with fixed data

The API tests need internet access and rely on existing data: users 1, 5, 10 and
posts 1, 50, 100. Offline tests (`pytest -m unit`) use a local HTTP server instead.

## JP-004: Malformed JSON causes a server error

```http
POST /posts
Content-Type: application/json

{not a json
```

The expected response is HTTP 400; the service returns HTTP 500 with a JSON parser stack
trace. `test_malformed_json_is_rejected` is marked `xfail(strict=True)`.
