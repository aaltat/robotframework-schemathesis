# Strict by default for operations that cannot be parsed

Schemathesis returns an error instead of an operation when it cannot parse one, and the
library used to drop those errors silently, so a schema whose operations mostly failed to
parse still produced a green run. We now report them, and the `strict` import argument
decides whether that is an error or a warning, defaulting to `True`.

## Considered options

Warning only, with no argument, was the obvious smaller change. It was rejected because a
warning in a CI log is exactly the thing nobody reads, and the problem being fixed is
precisely that reduced coverage goes unnoticed.

Defaulting `strict` to `False` would have made the change purely additive. It was rejected
for the same reason: the safe-looking default is the one that keeps the silent failure.

Letting `strict=False` also downgrade the "no test cases at all" error to a warning was
considered and rejected. `strict` answers "may I proceed with a schema I only partly
understand", which is a reasonable thing to say yes to. A suite with zero test cases
answers "is there anything to run at all", and nobody wants that to pass. Tying them
together would have reintroduced the silent green run through the new argument.

## Consequences

`strict=True` by default turns some currently green runs red without the user changing
anything. That is intended: the green was the bug. It is released as a feature rather than
a breaking change, consistent with the bug fixes released alongside it that have the same
effect.

Future problems that would silently reduce coverage, such as `path` and `url` both being
given, belong under this same argument rather than under new `fail_on_*` booleans.
