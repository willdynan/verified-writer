# verified-writer

A toolkit for writes you cannot afford to get wrong. Its thesis: an HTTP
200 is not proof — the read-back is.

APIs accept writes they do not perform. Fields drop silently. Whole
payloads get a 200 and vanish. Derived fields move on their own. When the
target is a system of record, "the call returned 200" and "the data is now
correct" are different claims. This toolkit refuses to conflate them.

## Quickstart

```
python3 -m unittest discover -s tests    # no dependencies
```

`DemoTarget` injects every failure mode the toolkit catches: silent field
drop, 200-but-noop, undeclared side effects. The tests double as a tour.

## Layout

```
verified_writer/target.py    the write target, and a demo that lies
verified_writer/ledger.py    append-only events, marks included
verified_writer/writer.py    preflight, staleness check, read-back diff
verified_writer/rollback.py  ledger entries only, idempotent
verified_writer/review.py    one-file approval page, works from file://
```

The walkthrough: [docs/design.md](docs/design.md). The rules:
[docs/rules.md](docs/rules.md). Limits and provenance:
[docs/lineage.md](docs/lineage.md). Distilled August 2026 from production
practice. The commit log starts at distillation.
