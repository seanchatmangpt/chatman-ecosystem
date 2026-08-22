from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.recovery_transaction.subject import Subject
from scripts.develop_train.recovery_transaction.context import RecoveryContext, digest_json
from scripts.develop_train.recovery_transaction.lease import Lease
from scripts.develop_train.recovery_transaction.attempt import RecoveryAttempt
from scripts.develop_train.recovery_transaction.engine import qualify
from scripts.develop_train.recovery_transaction.dependency import DependencyGraph
from scripts.develop_train.recovery_transaction.persistence import PersistenceNeed
from scripts.develop_train.recovery_transaction.recovery import RecoveryStrategy

NOW = datetime(2026, 8, 22, 17, 0, tzinfo=timezone.utc)
SUB = Subject("seanchatmangpt/chatman-ecosystem", "a" * 40)
CTX = RecoveryContext(SUB, 1, "cut-a", digest_json("p"), digest_json("f"), "LATEST_COMPLETE")
ATT = RecoveryAttempt("release-control", CTX, CTX, 1, NOW, Lease(NOW - timedelta(minutes=1), NOW + timedelta(minutes=5)), "n")

class T(unittest.TestCase):
    def test_dependency_failure_dominates_local_recovery(self):
        result = qualify(attempt=ATT, current=CTX, witness=None, strategy=RecoveryStrategy.CAS_RESELECT, graph=DependencyGraph({"release-control": ("gymact",), "gymact": ()}), standings={"gymact": "BUILD_BROKEN"}, persistence=PersistenceNeed(), now=NOW)
        self.assertEqual(result.standing, "BLOCKED")
        self.assertEqual(result.receipt.blockers, ("gymact",))
        self.assertFalse(result.receipt.actuation_performed)

if __name__ == "__main__":
    unittest.main()
