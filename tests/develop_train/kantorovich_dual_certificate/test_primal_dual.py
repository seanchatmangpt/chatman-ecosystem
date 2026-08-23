from fractions import Fraction as F
import unittest
from scripts.develop_train.kantorovich_dual_certificate import *
A=FiniteMeasure.from_mapping({"a":F(1,2),"b":F(1,3),"c":F(1,6)})
B=FiniteMeasure.from_mapping({"a":F(1,3),"b":F(1,3),"c":F(1,3)})
COST={(a,b):(0 if a==b else (1 if {a,b}!={"a","c"} else 2)) for a in ("a","b","c") for b in ("a","b","c")}
M=GroundMetric.from_mapping(("a","b","c"),COST)
class T(unittest.TestCase):
    def test_primal_dual_certificate(self):
        plan=solve_primal(A,B,M); dual=derive_dual(plan,A,B,M); cert=verify_certificate(A,B,M,plan,dual)
        self.assertEqual(cert.gap,0); self.assertTrue(cert.complementary_slackness); self.assertTrue(cert.weak_duality)
    def test_tampered_dual_refuses(self):
        plan=solve_primal(A,B,M); dual=DualPotential(tuple((k,F(99)) for k in A.support),tuple((k,F(0)) for k in B.support))
        with self.assertRaises(Refused): verify_certificate(A,B,M,plan,dual)
