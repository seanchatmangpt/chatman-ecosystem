import unittest
from fractions import Fraction as F
from scripts.release_train.kantorovich_dual_crown import *
class T(unittest.TestCase):
    def fixture(self):
        p=FiniteMeasure.of({"a":1}); q=FiniteMeasure.of({"b":1}); m=GroundMetric.of(("a","b"),((0,2),(2,0)))
        return p,q,m,TransportPlan.of([("a","b",1)]),DualPotential.of({"a":1},{"b":1})
    def test_strong_duality_and_slackness(self):
        c=verify_certificate(*self.fixture()); self.assertEqual(c.primal_cost,F(2)); self.assertEqual(c.max_slack,0)
    def test_gap_refuses(self):
        p,q,m,plan,_=self.fixture()
        with self.assertRaises(Refused): verify_certificate(p,q,m,plan,DualPotential.of({"a":0},{"b":0}))
