import unittest
from scripts.measure_train.delta.contradiction import contradictions,worst
class T(unittest.TestCase):
 def test_mixed_sensor_evidence_visible(self):
  self.assertEqual(contradictions([('ci','PASS'),('ci','FAIL')]),(('ci',('FAIL','PASS')),)); self.assertEqual(worst(['PASS','FAIL']),"FAIL")
