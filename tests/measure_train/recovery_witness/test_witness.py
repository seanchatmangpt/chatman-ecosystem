import unittest
from datetime import datetime,timezone
from scripts.measure_train.recovery_witness.subject import Subject,Refused
from scripts.measure_train.recovery_witness.context import RecoveryContext
from scripts.measure_train.recovery_witness.witness import CompatibilityWitness
class T(unittest.TestCase):
 def test_false_exact_refuses(self):
  c=RecoveryContext(Subject("o/r","a"*40),"c","1"*64,"2"*64,1)
  with self.assertRaises(Refused): CompatibilityWitness(c,c,"EXACT","PASS","w",datetime.now(timezone.utc),"3"*64,"4"*64)
