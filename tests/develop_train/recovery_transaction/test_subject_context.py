from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.recovery_transaction.subject import Subject, Refusal
from scripts.develop_train.recovery_transaction.context import RecoveryContext, digest_json

NOW = datetime(2026, 8, 22, 17, 0, tzinfo=timezone.utc)
SUB = Subject("seanchatmangpt/chatman-ecosystem", "a" * 40)

def ctx(gen=1, cut="cut-a", policy="p1", frontier="f1", strategy="LATEST_COMPLETE"):
    return RecoveryContext(SUB, gen, cut, digest_json(policy), digest_json(frontier), strategy)

class T(unittest.TestCase):
    def test_exact_subject_and_context_are_deterministic(self):
        self.assertEqual(SUB.identity, "seanchatmangpt/chatman-ecosystem@" + "a" * 40)
        self.assertEqual(ctx().digest, ctx().digest)
    def test_short_sha_and_negative_generation_refuse(self):
        with self.assertRaises(Refusal):
            Subject("a/b", "abc")
        with self.assertRaises(Refusal):
            RecoveryContext(SUB, -1, "c", "p", "f", "s")

if __name__ == "__main__":
    unittest.main()
