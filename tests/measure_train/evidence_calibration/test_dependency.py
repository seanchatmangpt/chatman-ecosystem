import unittest
from scripts.measure_train.evidence_calibration.dependency import propagate
class T(unittest.TestCase):
 def test_blocker(self):
  r=propagate(["c","p"],[("c","p")],{"c":"PARTIAL_ALIVE","p":"BUILD_BROKEN"})
  self.assertEqual(r["c"],"BLOCKED")
