import unittest
from fractions import Fraction as F
from scripts.release_train.kantorovich_dual_crown import Subject,FiniteMeasure,GroundMetric,Refused
class T(unittest.TestCase):
    def test_exact_identity_measure_metric(self):
        s=Subject("o/r","a"*40,"sem",3); self.assertEqual(s.generation,3)
        p=FiniteMeasure.of({"a":1,"b":1}); self.assertEqual(p.as_dict()["a"],F(1,2))
        m=GroundMetric.of(("a","b"),((0,2),(2,0))); self.assertEqual(m.cost("a","b"),2)
    def test_triangle_refuses(self):
        with self.assertRaises(Refused): GroundMetric.of(("a","b","c"),((0,1,3),(1,0,1),(3,1,0)))
