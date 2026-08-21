# verified-writer

![tests](https://github.com/willdynan/verified-writer/actions/workflows/tests.yml/badge.svg)

Every system of record I've automated has eventually lied to me. The API
said 200; the field I wrote was gone. The payload was "accepted" and
nothing changed. A column moved that nobody asked to move.

This is the toolkit I wish I'd had the first time. It treats every write
as a claim to prove, every approval as something that can go stale, and
every mutation as a thing that must carry its own undo — because when the
target is the system your auditors read, "probably fine" is an incident
report waiting for a timestamp.

The thesis in one line: **an HTTP 200 is not proof. The read-back is.**

## How it behaves

- Dry-run is the default. `live=True` is a decision you make at the call
  site, not a surprise you discover after the writes.
- The write scope gets probed before record one — read scope passing
  proves nothing about write scope.
- Every approval carries the record state the human saw. If the record
  moved since, that write is refused, loudly.
- The undo lands in an append-only ledger *before* the write does.
- After every write: read back, diff, and flag anything that moved beyond
  the payload. A verified write and a lying write both leave evidence.
- Rollback restores only what the ledger says this tool wrote, exactly
  once. Human edits in the target are untouchable from here.
- Approvals happen in one self-contained HTML file that works from
  `file://` on whatever machine the approver has.

## Quickstart

```
python3 -m unittest discover -s tests    # no dependencies
```

The demo target lies in every way the real ones did — silent field drops,
200-but-nothing, phantom side effects — and the suite catches each lie by
name. The tests are the tour.

## Going deeper

[docs/design.md](docs/design.md) walks the pieces with captured output.
[docs/rules.md](docs/rules.md) gives every rule its reason and its test.
[docs/lineage.md](docs/lineage.md) holds the honest limits and provenance.

Distilled August 2026 from production write paths that earned each rule
the hard way. The commit log starts at the distillation.
