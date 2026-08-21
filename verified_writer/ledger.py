"""Append-only JSONL ledger. Every state change is an appended event.

Rollback marks are events too, never in-place edits — a rewrite that holds the
marks in memory and writes the file back unmarked is a bug that has actually
shipped. Append-only makes that shape impossible: the second rollback reads the
first one's marks because nothing can unwrite them.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class Ledger:
    def __init__(self, path):
        self.path = Path(path)

    def append(self, event: dict) -> None:
        record = dict(event)
        record.setdefault("ts", datetime.now(timezone.utc).isoformat())
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def entries(self) -> list[dict]:
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        return [json.loads(line) for line in lines if line.strip()]

    def written_ids(self) -> set:
        return {e["record_id"] for e in self.entries() if e["event"] == "write"}

    def rolled_back_ids(self) -> set:
        return {e["record_id"] for e in self.entries() if e["event"] == "rollback"}

    def write_events(self) -> list[dict]:
        return [e for e in self.entries() if e["event"] == "write"]
