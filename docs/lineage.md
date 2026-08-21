---
type: Reference
title: Lineage
description: Honest limits and provenance.
---

# Honest limits

- The demo target runs in-process. Transport is deliberately out of
  scope — the pattern is everything around the write, not the write's
  plumbing.
- Per-record all-or-nothing, not cross-record transactions. None of the
  production targets offered transactions at all. A failed batch is a
  ledger you can read and a rollback you can run, not an automatic revert.
- The ledger is a local file, the authoritative record of what this tool
  did. Multi-writer coordination stays out of scope.

# Lineage

This is a distillation, not a port. The pattern matured across several
production write paths during 2026, each mutating a system of record that
other people trusted. Every rule here comes from a write that lied. One
target returned 200 and dropped a field. One scope read but refused to
write. One approval went stale between review and run. The rollback-mark
bug is real, found in review of a production tool. The targets,
populations, and counts stay out of this repo on purpose. The architecture
is the artifact, and the demo target is synthetic.

Distilled: August 2026. This repository began at distillation. The dates
above describe the pattern's history, not this commit log.
