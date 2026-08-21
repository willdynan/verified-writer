"""Scoped rollback: only what the ledger says this tool wrote, only once.

Anything changed by hand in the target is untouchable from here by design.
Restores are verified by read-back like any other write, and the rollback mark
is an appended event, so a second run finds nothing to do instead of
re-deleting work.
"""

from .ledger import Ledger


def rollback(target, ledger: Ledger, live: bool = False) -> list[dict]:
    done = ledger.rolled_back_ids()
    results = []
    for event in ledger.write_events():
        rid = event["record_id"]
        if rid in done:
            continue
        restore = {k: event["pre_state"].get(k) for k in event["payload"]}
        result = {"record_id": rid, "restore": restore}
        if not live:
            result["action"] = "dry_run"
            results.append(result)
            continue
        target.put(rid, restore)
        post = target.get(rid)
        missing = {k: v for k, v in restore.items() if post.get(k) != v}
        if missing:
            result.update(action="failed_verification", missing=missing)
        else:
            ledger.append({"event": "rollback", "record_id": rid})
            result["action"] = "rolled_back"
        results.append(result)
        done.add(rid)
    return results
