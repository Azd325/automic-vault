# ADR 0011: Allow Path Execution for Snapshot-Incompatible Interpreters

- Status: Accepted
- Date: 2026-08-11

## Context

ADR 0005 requires Blessed Scripts to execute from a verified snapshot so file
edits cannot race authorization. Some interpreters, including `uv run --script`,
cannot execute the `/dev/fd/N` snapshot. Sending the script through standard
input would consume input that belongs to the script. Treating the invocation as
a direct injection discards the user’s Blessing and its narrower authority.

## Decision

Automic Vault may execute a Blessed Script from its canonical path when its
interpreter appears on the snapshot-incompatible list. The blessing review
warns that another same-user process can change the script after verification
and before the interpreter opens it. The user overrides the snapshot requirement
by choosing **Bless Anyway**. Automic Vault verifies the exact contents against
the Blessing for every authorization request and prints the same warning before
every execution. The Blessing records this override. Existing Blessings do not
gain it during an upgrade and must be reviewed again.

Automic Vault preserves standard input and does not transform the interpreter
command. Interpreters not on the compatibility list continue to receive the
verified `/dev/fd/N` snapshot.

## Consequences

- The Blessing still binds the canonical path, exact contents, Script
  Declaration, capabilities, and Launcher Endorsements.
- Path execution has a time-of-check-to-time-of-use window that the verified
  snapshot normally removes.
- Adding an interpreter to the compatibility list requires a reproduction that
  demonstrates snapshot execution cannot work and tests for both warnings.

## System Python compatibility (2026-10-26)

The compatibility list also recognizes the explicit `/usr/bin/python3` argument,
including behind `/usr/bin/env`. Apple's Python 3.9.6 advances the shared file
offset while probing a `/dev/fd/N` script as a ZIP archive, then executes an empty
script and exits successfully. This reproduces without Automic Vault:

```sh
printf 'raise SystemExit(3)\n' > /tmp/av-python-snapshot.py
/usr/bin/python3 -I /dev/fd/9 9</tmp/av-python-snapshot.py  # exits 0 on 3.9.6
/usr/bin/python3 -I /tmp/av-python-snapshot.py             # exits 3
```

See [CPython #87235](https://github.com/python/cpython/issues/87235) and
[the upstream fix](https://github.com/python/cpython/pull/99768).
The CLI and blessing review recognize the same literal path without executing
an interpreter or its arguments before Approval. Bare `python3` resolved through
PATH, aliases, and other installations are not added to the exception. Fixed
Python installations at other paths retain verified-snapshot execution.

This reuses the existing explicit override, including re-review of old
Blessings and warnings during blessing and every execution. It grants no new
authority without that review. The static system-path entry remains an explicit
exception if Apple replaces its Python with a fixed build; removing that entry
can restore snapshots without broadening authority. Supporting other affected
installations requires a separately reviewed compatibility-list change.
