import unittest
from scripts.measure_train.cut_epoch.census import cut_census,standing
class T(unittest.TestCase):
 def test_failure_dominates_and_green_bounded(self):
  self.assertEqual(standing(cut_census((("a","PASS"),("a","FAIL")))) ,"BUILD_BROKEN")
  self.assertEqual(standing(cut_census((("a","PASS"),))),"PARTIAL_ALIVE")
