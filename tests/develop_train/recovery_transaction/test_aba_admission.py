from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.recovery_transaction.subject import Subject, Refusal
from scripts.develop_train.recovery_transaction.context import RecoveryContext, digest_json
from scripts.develop_train.recovery_transaction.lease import Lease
from scripts.develop_train.recovery_transaction.attempt import RecoveryAttempt
from scripts.develop_train.recovery_transaction.aba import Transition, detect_aba, refuse_aba
from scripts.develop_train.recovery_transaction.admission import admit_attempt
from scripts.develop_train.recovery_transaction.witness import CompatibilityWitness, WitnessKind

NOW = datetime(2026, 8, 22, 17, 0, tzinfo=timezone.utc)
SUB = Subject("seanchatmangpt/chatman-ecosystem", "a" * 40)

def ctx(gen=1, cut="A"):
    return RecoveryContext(SUB, gen, cut, digest_json(f"p{gen}"), digest_json(f"f{gen}"), "LATEST_COMPLETE")

def att(base, target):
    return RecoveryAttempt("release-control", base, target, target.generation, NOW, Lease(NOW - timedelta(minutes=1), NOW + timedelta(minutes=5)), f"n{target.generation}")

class T(unittest.TestCase):
    def test_aba_detects_reused_cut_id_with_new_generation(self):
        a, b, a2 = ctx(1, "A"), ctx(2, "B"), ctx(3, "A")
        transitions = [Transition(a, b), Transition(b, a2)]
        self.assertTrue(detect_aba(transitions))
        with self.assertRaises(Refusal):
            refuse_aba(transitions)
    def test_stale_target_and_stale_witness_refuse(self):
        a, b, c = ctx(1, "A"), ctx(2, "B"), ctx(3, "C")
        witness = CompatibilityWitness.between(a, b, WitnessKind.SEMANTIC_EQUIVALENT, {"proof": 1})
        with self.assertRaises(Refusal):
            admit_attempt(att(a, b), c, witness, NOW)
        with self.assertRaises(Refusal):
            admit_attempt(att(a, c), c, witness, NOW)

if __name__ == "__main__":
    unittest.main()
