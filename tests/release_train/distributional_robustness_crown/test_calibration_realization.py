import unittest
from scripts.release_train.distributional_robustness_crown.api import *
from scripts.release_train.distributional_robustness_crown.refusal import Refused
class T(unittest.TestCase):
 def test_current_and_realization(self):
  c=Calibration(2,10,.2,.3,"d"); self.assertEqual(current([Calibration(1,2,.4,.5,"x",False),c]),c)
  cases=[Realization(True,True,.1,0),Realization(False,False,.9,1)]; m=realization_metrics(cases); self.assertEqual(m["false_stable"],0); self.assertTrue(monotone_stress(cases))
  q=Cusum(.2,.1); self.assertFalse(q.observe(.1)); self.assertTrue(q.observe(.3))
 def test_split_current_refuses(self):
  with self.assertRaises(Refused): current([Calibration(1,2,.1,.2,"a"),Calibration(1,2,.2,.2,"b")])
