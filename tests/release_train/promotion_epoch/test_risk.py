import unittest
from scripts.release_train.promotion_epoch.risk import RiskVector
class T(unittest.TestCase):
 def test_score(self): self.assertEqual(RiskVector(1,5,5,5).score,14)
 def test_bounds(self):
  with self.assertRaises(ValueError): RiskVector(0,5,5,5)
