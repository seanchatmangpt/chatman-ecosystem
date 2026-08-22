import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.recovery_witness.subject import Subject
from scripts.measure_train.recovery_witness.context import RecoveryContext
from scripts.measure_train.recovery_witness.lease import WitnessLease
from scripts.measure_train.recovery_witness.proof import RecoveryProof
from scripts.measure_train.recovery_witness.receipt import manufacture_receipt
class T(unittest.TestCase):
 def test_deterministic_no_do(self):
  now=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject("o/r","a"*40); c=RecoveryContext(s,"a","1"*64,"2"*64,1)
  p=RecoveryProof("RESELECT",None,WitnessLease(now,now+timedelta(seconds=1)),"p")
  a=manufacture_receipt(s,c,c,p,"ADMITTED_RESELECT","UNKNOWN"); b=manufacture_receipt(s,c,c,p,"ADMITTED_RESELECT","UNKNOWN")
  self.assertEqual(a,b); self.assertFalse(a["body"]["actuation_performed"])
