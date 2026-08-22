from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.recovery_transaction.subject import Subject, Refusal
from scripts.develop_train.recovery_transaction.context import RecoveryContext, digest_json
from scripts.develop_train.recovery_transaction.lease import Lease
from scripts.develop_train.recovery_transaction.witness import CompatibilityWitness, WitnessKind

NOW = datetime(2026, 8, 22, 17, 0, tzinfo=timezone.utc)
SUB = Subject("seanchatmangpt/chatman-ecosystem", "a" * 40)

def ctx(gen=1, cut="cut-a"):
    return RecoveryContext(SUB, gen, cut, digest_json("p"), digest_json("f"), "LATEST_COMPLETE")

class T(unittest.TestCase):
    def test_false_exact_refuses_and_semantic_witness_binds_transition(self):
        before, after = ctx(), ctx(gen=2, cut="cut-b")
        with self.assertRaises(Refusal):
            CompatibilityWitness.between(before, after, WitnessKind.EXACT, {"proof": "x"})
        witness = CompatibilityWitness.between(before, after, WitnessKind.SEMANTIC_EQUIVALENT, {"proof": "x"})
        self.assertEqual(witness.before_digest, before.digest)
        self.assertEqual(witness.after_digest, after.digest)
    def test_half_open_lease(self):
        lease = Lease(NOW, NOW + timedelta(seconds=10))
        self.assertTrue(lease.active(NOW))
        self.assertFalse(lease.active(NOW + timedelta(seconds=10)))

if __name__ == "__main__":
    unittest.main()
