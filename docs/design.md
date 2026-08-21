---
type: Reference
title: Design notes
description: How the pieces fit together.
---

# Design notes

## What this is

Some writes are cheap to retry and nobody audits them. This toolkit is for
the other kind: mutations of a system of record that other people trust.
There, "the call returned 200" and "the data is now correct" are different
claims, and the gap between them is an incident.

The thesis in one line: **an HTTP 200 is not proof — the read-back is.**
APIs accept writes they do not perform. Fields drop silently. Whole
payloads get acknowledged and vanish. Server-side fields move on their
own. So the toolkit treats every write as a claim to verify. It treats
every approval as a snapshot that can go stale. It treats every mutation
as something that must carry its own undo.

## How it works

```
 changes (approved) --> apply(target, ledger, changes, live=?)
                           |
        1. can_write() probe          -- before record one
        2. expected_pre check         -- refuse stale approvals
        3. ledger: "pre" event        -- the undo exists first
        4. target.put()               -- the write
        5. target.get() + diff        -- the proof
        6. ledger: "write" event      -- or "verify_failed"

 rollback(target, ledger, live=?)     -- ledger entries only, once
 review.py                            -- one HTML file, approvals in, pre-state out
```

The ledger is append-only JSONL. Every state change is an appended event,
including rollback marks. Nothing edits in place, so nothing can lose a
mark by rewriting the file around it.

```json
{"event":"pre","record_id":"r1","pre_state":{"owner":"ada@example.com",
 "state":"open","revision":3},"payload_sha":"ab45..."}
{"event":"write","record_id":"r1","pre_state":{...},
 "payload":{"state":"closed"},"payload_sha":"ab45...","unexpected":["queue"]}
```

## Worked example

Real output. The demo target here accepts the write and also mutates a
`queue` field the payload never mentioned:

```
# dry run (the default)
[{"record_id": "r1", "action": "dry_run", "plan": {"state": "closed"}}]

# live
[{"record_id": "r1", "action": "written", "unexpected": ["queue"]}]

# rollback, live
[{"record_id": "r1", "restore": {"state": "open"}, "action": "rolled_back"}]
```

The write verified — every intended field landed — and the side effect is
on the record as `unexpected`. Declared derived fields (`revision`,
`updated_at`) move on every write and do not flag. The rollback restored
exactly the fields the tool wrote, nothing else.

Every rule and its citation: [rules.md](rules.md). Limits and provenance:
[lineage.md](lineage.md).
