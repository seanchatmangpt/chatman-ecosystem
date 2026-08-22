import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.recovery_witness.proof import RecoveryProof
from scripts.measure_train.recovery_witness.lease import WitnessLease
from scripts.measure_train.recovery_witness.subject import Refused
class T(unittest.TestCase):
 def test_witness_requirement(self):
  now=datetime.now(timezone.utc); lease=WitnessLease(now,now+timedelta(seconds=1))
  self.assertEqual(RecoveryProof("RESELECT",None,lease,"p").strategy,"RESELECT")
  with self.assertRaises(Refused): RecoveryProof("REBIND_EQUIVALENT",None,lease,"p")
