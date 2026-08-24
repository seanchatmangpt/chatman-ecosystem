from fractions import Fraction as F
import unittest
from scripts.develop_train.kantorovich_dual_certificate import *
A=FiniteMeasure.from_mapping({"a":F(1,2),"b":F(1,3),"c":F(1,6)})
B=FiniteMeasure.from_mapping({"a":F(1,3),"b":F(1,3),"c":F(1,3)})
COST={(a,b):(0 if a==b else (1 if {a,b}!={"a","c"} else 2)) for a in ("a","b","c") for b in ("a","b","c")}
M=GroundMetric.from_mapping(("a","b","c"),COST)
class T(unittest.TestCase):
    def test_three_support_ambiguity(self):
        ambiguity=WassersteinAmbiguity(A,F(1,3),M); cert=ambiguity.certificate(B)
        self.assertEqual(cert.gap,0); self.assertTrue(ambiguity.contains(B))
    def test_worst_case_certified(self):
        ambiguity=WassersteinAmbiguity(A,F(1,3),M); result=worst_case(ambiguity,{"a":0,"b":1,"c":3},denominator=6)
        self.assertLessEqual(result.distance,F(1,3)); self.assertEqual(result.certificate_gap,0)
