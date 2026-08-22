import unittest
from scripts.release_train.promotion_intent_lease.standing import aggregate,Standing
class T(unittest.TestCase):
 def test_failure_dominates(self):
  self.assertEqual(aggregate(('PASS','FAIL')),Standing.BUILD_BROKEN)
  self.assertEqual(aggregate(('PASS',)),Standing.PARTIAL_ALIVE)
  self.assertEqual(aggregate(('PASS','PENDING')),Standing.UNKNOWN)
