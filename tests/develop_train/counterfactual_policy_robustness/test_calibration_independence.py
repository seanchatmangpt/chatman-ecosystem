import unittest
from fractions import Fraction as F
from scripts.develop_train.counterfactual_policy_robustness.calibration import Calibration,require_current
from scripts.develop_train.counterfactual_policy_robustness.independence import EstimatorIdentity,IndependenceProof,require_independent
from scripts.develop_train.counterfactual_policy_robustness.errors import Refused
class TestCalibrationIndependence(unittest.TestCase):
    def test_current_calibration_and_independence(self):
        m=require_current([Calibration(1,'a',3,F(1,10)),Calibration(2,'b',4,F(1,20))]); self.assertEqual(m.generation,2); l=EstimatorIdentity('ips','a'); r=EstimatorIdentity('dr','b','m'); self.assertTrue(require_independent(IndependenceProof(l,r,True)).proven)
        with self.assertRaisesRegex(Refused,'DIVERGENT'): require_current([Calibration(2,'a',3,F(0)),Calibration(2,'b',3,F(0))])
        with self.assertRaisesRegex(Refused,'SHARED_IMPLEMENTATION'): require_independent(IndependenceProof(l,EstimatorIdentity('x','a'),True))
