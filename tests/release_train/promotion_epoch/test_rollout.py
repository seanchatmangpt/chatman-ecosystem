import unittest
from scripts.release_train.promotion_epoch.rollout import build_rollout
class T(unittest.TestCase):
 def test_no_do(self):
  stages=build_rollout(("a","b")); self.assertEqual([s.action for s in stages],["VERIFY","CONSTRUCT","VERIFY","CONSTRUCT"])
