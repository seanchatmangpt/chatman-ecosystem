import unittest
from scripts.measure_train.strategy_binding.standing import standing
class T(unittest.TestCase):
 def test_bounded(self):
  self.assertEqual(standing(["PASS"]),"PARTIAL_ALIVE")
  self.assertEqual(standing(["PASS","FAIL"]),"BUILD_BROKEN")
