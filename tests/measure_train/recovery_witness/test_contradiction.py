import unittest
from datetime import datetime,timezone
from scripts.measure_train.recovery_witness.subject import Subject
from scripts.measure_train.recovery_witness.context import RecoveryContext
from scripts.measure_train.recovery_witness.witness import CompatibilityWitness
from scripts.measure_train.recovery_witness.contradiction import contradictions
class T(unittest.TestCase):
 def test_pass_fail_visible(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); a=RecoveryContext(s,"a","1"*64,"2"*64,1); b=RecoveryContext(s,"b","1"*64,"3"*64,2)
  rows=[CompatibilityWitness(a,b,"SEMANTIC_EQUIVALENT","PASS","x",now,"4"*64,"5"*64),
        CompatibilityWitness(a,b,"BACKWARD_COMPATIBLE","FAIL","y",now,"4"*64,"5"*64)]
  self.assertEqual(len(contradictions(rows)),1)
