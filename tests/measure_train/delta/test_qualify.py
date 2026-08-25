import unittest
from scripts.measure_train.delta.qualify import qualify
class T(unittest.TestCase):
 def test_failure_unknown_and_success_ceiling(self):
  self.assertEqual(qualify(movement_material=True,ci_outcomes=['FAIL'],runtime_standing='UNKNOWN',stale=False,contradictions_rows=[]),'BUILD_BROKEN')
  self.assertEqual(qualify(movement_material=True,ci_outcomes=['PASS'],runtime_standing='PARTIAL_ALIVE',stale=False,contradictions_rows=[]),'PARTIAL_ALIVE')
  self.assertEqual(qualify(movement_material=True,ci_outcomes=['PASS'],runtime_standing='PARTIAL_ALIVE',stale=True,contradictions_rows=[]),'UNKNOWN')
