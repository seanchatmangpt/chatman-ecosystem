import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.recovery_witness.subject import Subject
from scripts.measure_train.recovery_witness.context import RecoveryContext
from scripts.measure_train.recovery_witness.witness import CompatibilityWitness
from scripts.measure_train.recovery_witness.frontier import current_witness_frontier
class T(unittest.TestCase):
 def test_new_generation_wins(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40)
  a=RecoveryContext(s,"a","1"*64,"2"*64,1); b=RecoveryContext(s,"b","1"*64,"3"*64,2)
  w1=CompatibilityWitness(a,a,"SEMANTIC_EQUIVALENT","PASS","w1",now,"4"*64,"4"*64)
  w2=CompatibilityWitness(a,b,"SEMANTIC_EQUIVALENT","PASS","w2",now+timedelta(seconds=1),"4"*64,"5"*64)
  self.assertIn(w2,current_witness_frontier([w1,w2]))
