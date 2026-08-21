---
type: Reference
title: Rules
description: The reasoning behind every rule.
---

# The rules, with their citations

Every rule exists because the easy version fails in a specific way. The
test file after each rule is the citation.

## Preflight the write scope (`tests/test_writer.py`)

`can_write()` runs before record one. Read scope passing proves nothing
about write scope. A 403 on the first record of a large batch is a
preflight. A 403 after a partial batch is an incident with a cleanup
phase.

## Refuse stale approvals (`tests/test_writer.py`)

Every change carries `expected_pre`: the field values the human approved
against. When the live record disagrees, the writer refuses that change
loudly and moves on. There is no "probably still fine". The approval page
exports exactly this shape, so what the human saw is what the writer
insists on.

## The undo exists before the write (`tests/test_writer.py`)

The `pre` event, with the full pre-state and a payload hash, lands in the
ledger before `put()` runs. A crash between the write and the `write`
event leaves the pre-state on disk. That is the half you cannot
reconstruct afterward.

## Read back and diff (`tests/test_writer.py`)

After every live write, the writer reads the record and diffs. Every
intended field must have landed. A silent drop or a write-nothing 200
becomes `failed_verification`, on the record, and does not count as
written. Any other moved field flags as `unexpected` unless declared
derived. A verified write and a flagged write both leave evidence.

## Dry-run is the default (`tests/test_writer.py`)

`live=True` is a decision at the call site, not a flag you discover after
the writes. A dry run touches nothing and appends nothing.

## Idempotent re-runs (`tests/test_writer.py`)

A record with a `write` event in the ledger skips on the next run. Ledger
state decides, not target state — the target may have moved for reasons
this tool does not own.

## Rollback stays scoped and runs once (`tests/test_rollback.py`)

Rollback restores exactly the fields this tool wrote, for exactly the
records in its ledger. Anything a human changed in the target stays
untouchable from here by design. Marks are events the tool appends. A
rewrite that holds rollback marks in memory and saves the file back
unmarked has shipped as a real bug. The append-only shape makes that bug
impossible, and the double-rollback test pins it.

## The approval gate is one file (`tests/test_review.py`)

`review.py` renders pending changes into a single HTML page: data inlined,
no server, no CDN, works from `file://`, keyboard-driven, decisions in
localStorage. Approval gates get used on whatever machine the approver
has. A page with a build step or a backend does not get used.

## Extending it

- **A real target** is one thin adapter: `get(id)`, `put(id, payload)`,
  `can_write()`. The HTTP shape (probe endpoint, GET, PUT) maps
  one-to-one.
- **Different derived fields**: pass your own set to `apply(derived=...)`.
  Anything the server moves on every write belongs there, and nothing
  else does.
- **Batch review**: `review.write_page(path, changes)` takes the same
  dicts the writer consumes, so one pipeline feeds both the human gate
  and the run.
