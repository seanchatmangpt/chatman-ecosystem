import unittest
from scripts.measure_train.consistent_cut.standing import standing
class T(unittest.TestCase):
 def test_green_is_bounded(self):
  self.assertEqual(standing((("p/r","REPOSITORY","PASS"),),()),"PARTIAL_ALIVE")
  self.assertEqual(standing((("p/r","REPOSITORY","FAIL"),),()),"BUILD_BROKEN")
