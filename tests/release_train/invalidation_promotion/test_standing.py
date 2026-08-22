import unittest
from scripts.release_train.invalidation_promotion.standing import next_standing
class T(unittest.TestCase):
 def test_failure_and_recovery(self):
  self.assertEqual(next_standing('ALIVE','PRODUCER_BUILD_BROKEN'),'BLOCKED')
  self.assertEqual(next_standing('BLOCKED','PRODUCER_RECOVERED_REQUALIFY'),'REQUALIFYING')
  self.assertEqual(next_standing('ALIVE','SUPERSEDED_RECEIPT'),'UNKNOWN')
