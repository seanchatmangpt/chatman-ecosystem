import unittest
from scripts.develop_train.evidence_realization_control import *
class T(unittest.TestCase):
 def test_regret_observed_only(self): self.assertAlmostEqual(observed_regret(.6,[.7,.5]),.1,places=12)
 def test_no_counterfactual(self):
  with self.assertRaises(Refused): observed_regret(.6,[])
 def test_calibration(self): self.assertEqual(Calibration.from_observations([0,.7,0,0],[0,.1,.2,.1]).support,4)
