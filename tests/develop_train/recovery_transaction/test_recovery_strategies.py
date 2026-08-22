from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.recovery_transaction.subject import Subject, Refusal
from scripts.develop_train.recovery_transaction.context import RecoveryContext, digest_json
from scripts.develop_train.recovery_transaction.lease import Lease
from scripts.develop_train.recovery_transaction.attempt import RecoveryAttempt
from scripts.develop_train.recovery_transaction.recovery import RecoveryStrategy, decide
from scripts.develop_train.recovery_transaction.witness import CompatibilityWitness, WitnessKind

NOW = datetime(2026, 8, 22, 17, 0, tzinfo=timezone.utc)
SUB = Subject("seanchatmangpt/chatman-ecosystem", "a" * 40)

def ctx(gen=1, cut="A"):
    return RecoveryContext(SUB, gen, cut, digest_json(f"p{gen}"), digest_json(f"f{gen}"), "LATEST_COMPLETE")

def att(base, target):
    return RecoveryAttempt("release-control", base, target, 1, NOW, Lease(NOW - timedelta(minutes=1), NOW + timedelta(minutes=5)), "n")

class T(unittest.TestCase):
    def test_three_strategies_remain_distinct_and_never_alive(self):
        before, after = ctx(), ctx(2, "B")
        witness = CompatibilityWitness.between(before, after, WitnessKind.SEMANTIC_EQUIVALENT, {"proof": 1})
        results = [decide(strategy, att(before, after), witness) for strategy in RecoveryStrategy]
        self.assertEqual({result.reuse_allowed for result in results}, {False, True})
        self.assertTrue(all(result.standing == "REQUALIFYING" for result in results))
    def test_backward_compatible_cannot_equivalence_rebind(self):
        before, after = ctx(), ctx(2, "B")
        witness = CompatibilityWitness.between(before, after, WitnessKind.BACKWARD_COMPATIBLE, {"proof": 1})
        with self.assertRaises(Refusal):
            decide(RecoveryStrategy.VALIDATE_REBIND, att(before, after), witness)

if __name__ == "__main__":
    unittest.main()
