# SchemathesisLibrary

A Robot Framework test library that turns an OpenAPI schema into Robot Framework test
cases, using Schemathesis to generate them and DataDriver to present them as tests.

## Language

**Operation**:
A single path and method pair in the OpenAPI schema, such as `GET /user/{userid}`. This is
what Schemathesis generates test cases for.
_Avoid_: Endpoint, route, API call

**Unparseable operation**:
An operation Schemathesis could not turn into test cases, because of an unresolvable
reference or a malformed parameter for example. It is never tested, whatever happens next.
_Avoid_: Invalid operation, broken endpoint, failed operation

**Case**:
One generated request for one operation. Every case becomes exactly one Robot Framework
test, and a case is what the `${case}` test argument holds.
_Avoid_: Example, sample, test data row

**Strict**:
Whether a condition that would otherwise silently reduce test coverage is an error rather
than a warning. It never covers conditions that make the run meaningless, such as no test
cases being generated at all, which are always errors.
_Avoid_: Fail fast, safe mode, validation

**Sanitization**:
Replacing credentials with `[Filtered]` before anything reaches the Robot Framework log.
Which values count as sensitive is Schemathesis' decision, not this library's.
_Avoid_: Masking, redaction, scrubbing

## Test assets

**Subject suite**:
A suite in `atest/library/` that uses the library for real. It is the thing under test, not
a test of its own.
_Avoid_: Library test, inner suite

**Checker suite**:
A suite in `atest/test/` that runs a subject suite in a subprocess and asserts over the
`output.xml` it produced. Its name matches the subject suite it runs.
_Avoid_: Runner, outer test, wrapper suite

**Test app schema**:
The schema downloaded from the running test app into `atest/specs/test-app/`. It is
regenerated on every run and never committed.
_Avoid_: Spec file, openapi.json

**Hand written schema**:
A schema committed directly in `atest/specs/`, written to exercise a case the test app
cannot produce, such as an operation that cannot be parsed.
_Avoid_: Fixture, mock schema, stub
