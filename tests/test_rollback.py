import tempfile
import unittest
from pathlib import Path

from verified_writer.ledger import Ledger
from verified_writer.rollback import rollback
from verified_writer.target import DemoTarget
from verified_writer.writer import Change, apply

RECORDS = {
    "r1": {"owner": "ada@example.com", "state": "open", "revision": 3},
    "r2": {"owner": "bo@example.com", "state": "open", "revision": 1},
}


class Rollback(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self.dir.name) / "ledger.jsonl")
        self.target = DemoTarget(RECORDS)
        apply(self.target, self.ledger, [Change("r1", {"state": "closed"})], live=True)

    def tearDown(self):
        self.dir.cleanup()

    def test_dry_run_default_restores_nothing(self):
        results = rollback(self.target, self.ledger)
        self.assertEqual(results[0]["action"], "dry_run")
        self.assertEqual(self.target.get("r1")["state"], "closed")

    def test_live_restores_only_the_written_fields(self):
        results = rollback(self.target, self.ledger, live=True)
        self.assertEqual(results[0]["action"], "rolled_back")
        record = self.target.get("r1")
        self.assertEqual(record["state"], "open")
        self.assertEqual(record["owner"], "ada@example.com")

    def test_hand_made_changes_are_untouchable(self):
        # A human changed r2 in the target UI. It is not in the ledger.
        self.target.records["r2"]["state"] = "closed"
        results = rollback(self.target, self.ledger, live=True)
        self.assertEqual([r["record_id"] for r in results], ["r1"])
        self.assertEqual(self.target.get("r2")["state"], "closed")

    def test_double_rollback_finds_nothing_to_do(self):
        # The mark must survive as an appended event; an in-memory mark that a
        # rewrite discards is a bug that has shipped in the wild.
        rollback(self.target, self.ledger, live=True)
        puts_before = self.target.puts
        results = rollback(self.target, self.ledger, live=True)
        self.assertEqual(results, [])
        self.assertEqual(self.target.puts, puts_before)


if __name__ == "__main__":
    unittest.main()
