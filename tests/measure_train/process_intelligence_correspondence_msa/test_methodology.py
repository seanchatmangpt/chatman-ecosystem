import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.methodology import coverage,REQUIRED
class T(unittest.TestCase):
 def test_complete(self):
  self.assertTrue(coverage(REQUIRED)["complete"])
  self.assertFalse(coverage(REQUIRED[:-1])["complete"])
