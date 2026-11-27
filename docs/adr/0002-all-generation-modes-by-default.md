# All generation modes by default

Users copy `schemathesis.toml` settings from the Schemathesis documentation, where every
generation mode runs unless `mode` limits it. If the library generated fewer modes than the
file asks for, it would test less than the user expects, and the run would not tell them
([#338](https://github.com/aaltat/robotframework-schemathesis/issues/338),
[#341](https://github.com/aaltat/robotframework-schemathesis/issues/341)).

The library generates cases in every mode configured for an operation, and in positive and
negative mode when nothing sets `mode`. It reads `max-examples` and `mode` per operation, as
Schemathesis does in its fuzzing phase, so the top-level `[generation]` table, a `[[project]]`
block whose `title` matches the schema `info.title`, and `[[operations]]` entries all apply.
The library `max_examples` argument wins over `max-examples` in the file, as `base_url` and
`tls_verify` win over theirs. With neither, an operation gets 100 cases.

## Considered options

Positive-only as the library default, with negative cases on request, would keep existing
suites green. We rejected it because users configure the library from the Schemathesis
documentation, and the library would generate less than that documentation describes.

A separate set of cases per mode, each with its own `max-examples`, would double the tests in
a suite. We rejected it because Schemathesis counts `max-examples` across all modes: a user who
shares one `schemathesis.toml` between the CLI and Robot Framework would get twice as many
cases per operation in Robot Framework.

Letting `max-examples` in the file win over the library argument would ignore a value written
in the suite itself, and the log would not say so. We rejected it because the other library
arguments win over the file, and one rule is easier to remember than one per argument.

## Consequences

Suites without `mode` send invalid requests. A test with invalid data fails when the API
accepts it, or rejects it with a status that the schema does not document or that
`expected-statuses` under `[checks.negative_data_rejection]` does not list. `mode = "positive"`
sends valid requests only, for the whole suite or, under `[[operations]]`, for selected
operations.

Test names include the mode, as in `POST /items - negative - 5mK2pQ`, because the report for a
failure such as an undocumented status does not say that the request was invalid on purpose.

We release this without a major version bump, consistent with
[0001](0001-strict-by-default-for-unparseable-operations.md). The new failures show an API that
accepts invalid data, crashes on it, or answers with a response outside the schema or
`expected-statuses`. A suite that sets both `max_examples` on the Library line and
`max-examples` in the file gets the Library value, so its number of cases changes on upgrade.

The subject suites in `atest/library/` check library mechanics, such as auth and hooks, against
valid requests, so `atest/library/schemathesis.toml` sets `mode = "positive"` for them. The
`negative_cases` suite runs without `mode`, against an operation that accepts invalid data.
