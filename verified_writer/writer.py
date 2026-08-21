"""The write path. An HTTP 200 is not proof; the read-back is.

Order per change: refuse stale approvals, snapshot pre-state into the ledger,
write, read back, diff. The intended fields must all have landed; any other
moved field flags as UNEXPECTED unless declared derived. Dry-run is the
default — `live=True` is a decision, not a flag you discover.
"""

import hashlib
import json
from dataclasses import dataclass, field

from .ledger import Ledger

DERIVED = frozenset({"revision", "updated_at"})


class ScopeError(RuntimeError):
    pass


@dataclass
class Change:
    record_id: str
    payload: dict
    expected_pre: dict = field(default_factory=dict)


def _sha(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def apply(target, ledger: Ledger, changes, live: bool = False, derived=DERIVED) -> list[dict]:
    if live and not target.can_write():
        # Probe before the first write: read scope passing proves nothing
        # about write scope.
        raise ScopeError("target refuses writes; fix the credential before approving a run")
    already = ledger.written_ids()
    results = []
    for change in changes:
        result = {"record_id": change.record_id}
        pre = target.get(change.record_id)
        if pre is None:
            result.update(action="error", reason="record not found")
            results.append(result)
            continue
        if change.record_id in already:
            result.update(action="skip", reason="already written per ledger")
            results.append(result)
            continue
        stale = {k: (v, pre.get(k)) for k, v in change.expected_pre.items() if pre.get(k) != v}
        if stale:
            result.update(action="refused_stale", mismatches=stale)
            results.append(result)
            continue
        if not live:
            result.update(action="dry_run", plan=change.payload)
            results.append(result)
            continue
        ledger.append({"event": "pre", "record_id": change.record_id,
                       "pre_state": pre, "payload_sha": _sha(change.payload)})
        target.put(change.record_id, change.payload)
        post = target.get(change.record_id)
        missing = {k: (v, post.get(k)) for k, v in change.payload.items() if post.get(k) != v}
        unexpected = sorted(
            k for k in set(pre) | set(post)
            if pre.get(k) != post.get(k) and k not in change.payload and k not in derived
        )
        if missing:
            ledger.append({"event": "verify_failed", "record_id": change.record_id,
                           "missing": {k: list(v) for k, v in missing.items()}})
            result.update(action="failed_verification", missing=missing)
        else:
            ledger.append({"event": "write", "record_id": change.record_id,
                           "pre_state": pre, "payload": change.payload,
                           "payload_sha": _sha(change.payload), "unexpected": unexpected})
            result.update(action="written", unexpected=unexpected)
        results.append(result)
    return results
