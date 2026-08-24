from fractions import Fraction as F
import unittest
from scripts.develop_train.kantorovich_dual_certificate import *
S=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40+"#"+"b"*64)
COST={(a,b):(0 if a==b else (1 if {a,b}!={"a","c"} else 2)) for a in ("a","b","c") for b in ("a","b","c")}
M=GroundMetric.from_mapping(("a","b","c"),COST)
class T(unittest.TestCase):
    def test_identity_metric(self):
        self.assertEqual(S.repository,"seanchatmangpt/chatman-ecosystem"); self.assertEqual(M.cost("a","c"),2)
        with self.assertRaises(Refused): Subject.parse("x/y@abc")
    def test_triangle_refusal(self):
        bad=dict(COST); bad[("a","c")]=bad[("c","a")]=5
        with self.assertRaises(Refused): GroundMetric.from_mapping(("a","b","c"),bad)
