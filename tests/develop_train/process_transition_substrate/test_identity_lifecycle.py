import unittest
from scripts.develop_train.process_transition_substrate import *
class T(unittest.TestCase):
 def test_identity_transition(self):
  s=SubjectEpoch("seanchatmangpt/chatman-ecosystem@"+"a"*40,1); self.assertEqual(s.advance().generation,2); SubjectTransition(s,s.advance())
  with self.assertRaises(Refused): SubjectEpoch("bad@abc",0)
 def test_lifecycle(self):
  b=Obligation("reactor",State.FAIL,"ci"); a=Obligation("reactor",State.PASS,"ci")
  self.assertIsInstance(classify(b,a,"f"*64),Discharge)
  self.assertIsInstance(classify(a,b),Regression)
