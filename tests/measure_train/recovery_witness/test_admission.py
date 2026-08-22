import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.recovery_witness.subject import Subject,Refused
from scripts.measure_train.recovery_witness.context import RecoveryContext
from scripts.measure_train.recovery_witness.witness import CompatibilityWitness
from scripts.measure_train.recovery_witness.lease import WitnessLease
from scripts.measure_train.recovery_witness.proof import RecoveryProof
from scripts.measure_train.recovery_witness.admission import admit_recovery
class T(unittest.TestCase):
 def test_backward_not_equivalence(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40)
  a=RecoveryContext(s,"a","1"*64,"2"*64,1); b=RecoveryContext(s,"b","1"*64,"3"*64,2)
  w=CompatibilityWitness(a,b,"BACKWARD_COMPATIBLE","PASS","w",now,"4"*64,"5"*64)
  p=RecoveryProof("REBIND_EQUIVALENT",w,WitnessLease(now-timedelta(seconds=1),now+timedelta(seconds=5)),"p")
  with self.assertRaises(Refused): admit_recovery(p,a,b,(w,),now)
