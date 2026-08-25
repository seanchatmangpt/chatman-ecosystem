import unittest
from scripts.release_train.calibrated_composition_crown import *
class T(unittest.TestCase):
 def test_identity_interval(self):
  s=Subject.parse("a/b","a"*40,"b"*64); self.assertIn("@",s.key)
  self.assertAlmostEqual(Interval(.7,.9).frechet_and(Interval(.6,.8)).lo,.3)
 def test_invalid(self):
  with self.assertRaises(Refused): Subject.parse("a/b","x","b"*64)
