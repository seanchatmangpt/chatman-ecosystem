import unittest
from scripts.measure_train.acquisition_realization.regret import TrialUtility,ex_post_regret
class T(unittest.TestCase):
 def test_observed_counterfactual_regret(self):
  rows=[TrialUtility("a",0.2,2),TrialUtility("b",0.4,2)]
  self.assertAlmostEqual(ex_post_regret("a",rows),0.1)
  self.assertEqual(ex_post_regret("b",rows),0.0)
