# All generation modes by default

Users write `schemathesis.toml` from the Schemathesis documentation, where every generation
mode runs unless `mode` says otherwise. A library that generates fewer modes than the file
asks for tests less than the user expects, and nothing in the run says so.

The library generates cases in every generation mode configured for an operation. Without
a configured `mode`, that means positive and negative cases, as in Schemathesis. It reads
`max-examples` and `mode` per operation from the loaded schema config, so the top-level
`[generation]` table, a `[[project]]` block matched by `info.title` and `[[operations]]` all
apply.

## Considered options

Keeping positive-only as the library default, with negative cases only on request, would
have kept existing suites green. We rejected it because the library would then disagree
with the documentation users configure it from.

A separate set of cases per mode, each with its own `max-examples`, would double the number
of tests in a suite without the user asking for more. We rejected it: `max-examples` counts
cases across all modes.

## Consequences

Suites without `mode` send invalid requests. A test with invalid data fails when the API
accepts it, or rejects it with a status the schema does not document, such as the 400 that
FastAPI returns for a malformed body. `mode = "positive"` sends valid requests only.

We release this without a major version bump, consistent with
[0001](0001-strict-by-default-for-unparseable-operations.md): a suite that turns red found an
API that accepts invalid data, or a response the schema does not document.

The subject suites in `atest/library/` check library mechanics such as auth, hooks and
logging against valid requests, so `atest/library/schemathesis.toml` sets
`mode = "positive"` for them.
