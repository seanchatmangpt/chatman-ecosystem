import unittest
from scripts.release_train.realized_policy_admission.moments import Moments
class T(unittest.TestCase):
    def test_online_moments(self):
        m=Moments()
        for x in (1,2,3): m=m.add(x)
        self.assertEqual(m.n,3); self.assertAlmostEqual(m.mean,2); self.assertAlmostEqual(m.variance,1)
        self.assertLess(m.lower_confidence(),m.mean)
