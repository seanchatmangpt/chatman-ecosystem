import unittest
from datetime import datetime,timezone
from scripts.release_train.calibrated_recovery_quorum.witness import RecoveryWitness
from scripts.release_train.calibrated_recovery_quorum.standing import bounded_standing
from scripts.release_train.calibrated_recovery_quorum.sequential import SequentialDecision
class T(unittest.TestCase):
 def test_failure_dominates(self):
  w=RecoveryWitness("a","a"*64,"FAIL",datetime.now(timezone.utc)); self.assertEqual(bounded_standing([w],[{"admitted":True}],SequentialDecision(3,"ACCEPT_BOUNDED"),2,2,[]),"BUILD_BROKEN")
