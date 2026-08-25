import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.recovery_witness.proof import RecoveryProof
from scripts.measure_train.recovery_witness.lease import WitnessLease
from scripts.measure_train.recovery_witness.standing import standing
class T(unittest.TestCase):
 def test_reselect_not_alive(self):
  now=datetime.now(timezone.utc); p=RecoveryProof("RESELECT",None,WitnessLease(now,now+timedelta(seconds=1)),"p")
  self.assertEqual(standing((p,)),"UNKNOWN")
