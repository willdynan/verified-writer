"""The write target: a small protocol, and a demo that lies.

DemoTarget injects the failure modes this toolkit exists to catch, each seen
in a real system: a 200 that dropped a field, a 200 that wrote nothing at all,
server-side derived fields that change on every write, and side effects the
payload never asked for.
"""

from datetime import datetime, timezone


class DemoTarget:
    def __init__(self, records: dict, *, drop_fields=(), noop=False, side_effects=None):
        self.records = {rid: dict(rec) for rid, rec in records.items()}
        self.drop_fields = set(drop_fields)
        self.noop = noop
        self.side_effects = dict(side_effects or {})
        self.write_scope = True
        self.puts = 0

    def get(self, record_id: str) -> dict | None:
        rec = self.records.get(record_id)
        return dict(rec) if rec is not None else None

    def can_write(self) -> bool:
        return self.write_scope

    def put(self, record_id: str, payload: dict) -> dict:
        if not self.write_scope:
            raise PermissionError("write scope missing")
        self.puts += 1
        if self.noop:
            return {"status": 200}  # accepted, wrote nothing
        rec = self.records[record_id]
        for key, value in payload.items():
            if key not in self.drop_fields:  # accepted, silently dropped
                rec[key] = value
        rec.update(self.side_effects)
        rec["revision"] = rec.get("revision", 0) + 1
        rec["updated_at"] = datetime.now(timezone.utc).isoformat()
        return {"status": 200}
