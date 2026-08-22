import unittest
from scripts.measure_train.provenance.dependency import dependency_standing
class T(unittest.TestCase):
 def test_blocker(self):
  x=dependency_standing(["a","b"],[("a","b")],{"a":"PARTIAL_ALIVE","b":"BUILD_BROKEN"})
  self.assertEqual(x["a"],"BLOCKED")
