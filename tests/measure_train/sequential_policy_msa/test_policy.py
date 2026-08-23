import unittest
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.refusal import Refused
class T(unittest.TestCase):
 def test_policy(self):
  p=PolicyIdentity("p",1,"1"*64,"MAX_INFORMATION")
  self.assertEqual(p.generation,1)
  with self.assertRaises(Refused): PolicyIdentity("p",1,"1"*64,"MAGIC")
