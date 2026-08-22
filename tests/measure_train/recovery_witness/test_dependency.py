import unittest
from scripts.measure_train.recovery_witness.dependency import propagate
class T(unittest.TestCase):
 def test_build_broken_blocks(self):
  result=propagate(["a","b"],[("a","b")],{"a":"PARTIAL_ALIVE","b":"BUILD_BROKEN"})
  self.assertEqual(result["a"],"BLOCKED")
