import unittest
from scripts.measure_train.fusion_realization_msa.dependency import propagate
class T(unittest.TestCase):
 def test_broken_dependency_blocks(self):
  r=propagate(["consumer","producer"],[("consumer","producer")],{"consumer":"PARTIAL_ALIVE","producer":"BUILD_BROKEN"})
  self.assertEqual(r["consumer"],"BLOCKED")
