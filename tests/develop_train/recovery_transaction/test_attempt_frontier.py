from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.recovery_transaction.subject import Subject, Refusal
from scripts.develop_train.recovery_transaction.context import RecoveryContext, digest_json
from scripts.develop_train.recovery_transaction.lease import Lease
from scripts.develop_train.recovery_transaction.attempt import RecoveryAttempt
from scripts.develop_train.recovery_transaction.frontier import AttemptFrontier

NOW = datetime(2026, 8, 22, 17, 0, tzinfo=timezone.utc)
SUB = Subject("seanchatmangpt/chatman-ecosystem", "a" * 40)

def ctx(gen=1, cut="a"):
    return RecoveryContext(SUB, gen, cut, digest_json("p"), digest_json("f"), "LATEST_COMPLETE")

def att(base, target, ordinal, nonce):
    return RecoveryAttempt("release-control", base, target, ordinal, NOW, Lease(NOW - timedelta(minutes=1), NOW + timedelta(minutes=5)), nonce)

class T(unittest.TestCase):
    def test_frontier_preserves_history_and_deduplicates(self):
        a = ctx()
        one = att(a, a, 1, "one")
        two = att(a, a, 2, "two")
        frontier = AttemptFrontier.build([one, two, two])
        self.assertEqual(frontier.current, (two,))
        self.assertEqual(frontier.historical, (one,))
    def test_divergent_current_targets_refuse(self):
        a, b = ctx(), ctx(2, "b")
        with self.assertRaises(Refusal):
            AttemptFrontier.build([att(a, a, 2, "one"), att(a, b, 2, "two")])

if __name__ == "__main__":
    unittest.main()
