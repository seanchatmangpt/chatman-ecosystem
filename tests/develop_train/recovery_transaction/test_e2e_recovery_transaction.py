from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.recovery_transaction.subject import Subject, Refusal
from scripts.develop_train.recovery_transaction.context import RecoveryContext, digest_json
from scripts.develop_train.recovery_transaction.lease import Lease
from scripts.develop_train.recovery_transaction.attempt import RecoveryAttempt
from scripts.develop_train.recovery_transaction.engine import qualify
from scripts.develop_train.recovery_transaction.dependency import DependencyGraph
from scripts.develop_train.recovery_transaction.persistence import PersistenceNeed
from scripts.develop_train.recovery_transaction.recovery import RecoveryStrategy
from scripts.develop_train.recovery_transaction.witness import CompatibilityWitness, WitnessKind
from scripts.develop_train.recovery_transaction.receipt import replay

NOW = datetime(2026, 8, 22, 17, 0, tzinfo=timezone.utc)
SUB = Subject("seanchatmangpt/chatman-ecosystem", "a" * 40)

def ctx(gen, cut, policy):
    return RecoveryContext(SUB, gen, cut, digest_json(policy), digest_json(f"frontier-{gen}"), "LATEST_COMPLETE")

class T(unittest.TestCase):
    def test_current_witness_recovery_then_context_move_refuses(self):
        base = ctx(3, "cut-3", "p1")
        target = ctx(4, "cut-4", "p2")
        witness = CompatibilityWitness.between(base, target, WitnessKind.SEMANTIC_EQUIVALENT, {"proof": "verified"})
        attempt = RecoveryAttempt("release-control", base, target, 4, NOW, Lease(NOW - timedelta(minutes=1), NOW + timedelta(minutes=5)), "recover-4")
        result = qualify(attempt=attempt, current=target, witness=witness, strategy=RecoveryStrategy.VALIDATE_REBIND, graph=DependencyGraph({"release-control": ()}), standings={}, persistence=PersistenceNeed(durable=True), now=NOW)
        self.assertEqual(result.standing, "REQUALIFYING")
        self.assertTrue(replay(result.receipt, result.receipt.digest))
        self.assertFalse(result.receipt.actuation_performed)
        moved = ctx(5, "cut-5", "p3")
        with self.assertRaises(Refusal):
            qualify(attempt=attempt, current=moved, witness=witness, strategy=RecoveryStrategy.VALIDATE_REBIND, graph=DependencyGraph({"release-control": ()}), standings={}, persistence=PersistenceNeed(durable=True), now=NOW)

if __name__ == "__main__":
    unittest.main()
