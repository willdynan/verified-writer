import tempfile
import unittest
from pathlib import Path

from verified_writer.ledger import Ledger
from verified_writer.target import DemoTarget
from verified_writer.writer import Change, ScopeError, apply

RECORDS = {
    "r1": {"owner": "ada@example.com", "state": "open", "revision": 3},
    "r2": {"owner": "bo@example.com", "state": "open", "revision": 1},
}


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self.dir.name) / "ledger.jsonl")

    def tearDown(self):
        self.dir.cleanup()


class DryRunDefault(Base):
    def test_no_live_flag_means_no_writes(self):
        target = DemoTarget(RECORDS)
        results = apply(target, self.ledger, [Change("r1", {"state": "closed"})])
        self.assertEqual(results[0]["action"], "dry_run")
        self.assertEqual(target.puts, 0)
        self.assertEqual(target.get("r1")["state"], "open")
        self.assertEqual(self.ledger.entries(), [], "a dry run leaves no ledger events")


class Preflight(Base):
    def test_missing_write_scope_stops_before_any_write(self):
        target = DemoTarget(RECORDS)
        target.write_scope = False
        with self.assertRaises(ScopeError):
            apply(target, self.ledger, [Change("r1", {"state": "closed"})], live=True)
        self.assertEqual(target.puts, 0)


class ReadBack(Base):
    def test_silent_field_drop_is_caught(self):
        target = DemoTarget(RECORDS, drop_fields={"owner"})
        results = apply(target, self.ledger,
                        [Change("r1", {"owner": "cy@example.com", "state": "closed"})], live=True)
        self.assertEqual(results[0]["action"], "failed_verification")
        self.assertIn("owner", results[0]["missing"])
        events = [e["event"] for e in self.ledger.entries()]
        self.assertEqual(events, ["pre", "verify_failed"],
                         "pre-state lands before the write; the failure is on the record")

    def test_200_that_wrote_nothing_is_caught(self):
        target = DemoTarget(RECORDS, noop=True)
        results = apply(target, self.ledger, [Change("r1", {"state": "closed"})], live=True)
        self.assertEqual(results[0]["action"], "failed_verification")

    def test_unexpected_side_effect_is_flagged(self):
        target = DemoTarget(RECORDS, side_effects={"queue": "recalc"})
        results = apply(target, self.ledger, [Change("r1", {"state": "closed"})], live=True)
        self.assertEqual(results[0]["action"], "written")
        self.assertEqual(results[0]["unexpected"], ["queue"])

    def test_derived_fields_do_not_flag(self):
        target = DemoTarget(RECORDS)
        results = apply(target, self.ledger, [Change("r1", {"state": "closed"})], live=True)
        self.assertEqual(results[0]["action"], "written")
        self.assertEqual(results[0]["unexpected"], [],
                         "revision/updated_at are declared derived")


class StaleApprovals(Base):
    def test_pre_state_drift_refuses_loudly(self):
        target = DemoTarget(RECORDS)
        target.records["r1"]["state"] = "escalated"  # changed since approval
        results = apply(target, self.ledger,
                        [Change("r1", {"state": "closed"}, expected_pre={"state": "open"})],
                        live=True)
        self.assertEqual(results[0]["action"], "refused_stale")
        self.assertEqual(target.puts, 0)

    def test_matching_pre_state_proceeds(self):
        target = DemoTarget(RECORDS)
        results = apply(target, self.ledger,
                        [Change("r1", {"state": "closed"}, expected_pre={"state": "open"})],
                        live=True)
        self.assertEqual(results[0]["action"], "written")


class Idempotence(Base):
    def test_second_run_skips_written_records(self):
        target = DemoTarget(RECORDS)
        apply(target, self.ledger, [Change("r1", {"state": "closed"})], live=True)
        results = apply(target, self.ledger, [Change("r1", {"state": "closed"})], live=True)
        self.assertEqual(results[0]["action"], "skip")
        self.assertEqual(target.puts, 1)


if __name__ == "__main__":
    unittest.main()
