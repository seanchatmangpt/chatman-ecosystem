import unittest
from scripts.develop_train.ack_discharge.failure import *
class T(unittest.TestCase):
 def test_replay(self):
  p=FailurePlan(7,.5,3);self.assertEqual(simulate_delivery(['b','a','c'],p),simulate_delivery(['b','a','c'],p))
