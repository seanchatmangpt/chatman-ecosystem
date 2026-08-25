import unittest
from scripts.measure_train.recovery_witness.subject import Subject,Refused
from scripts.measure_train.recovery_witness.context import RecoveryContext
class T(unittest.TestCase):
 def test_context_digest_and_generation(self):
  c=RecoveryContext(Subject("o/r","a"*40),"cut","1"*64,"2"*64,1)
  self.assertEqual(len(c.digest),64)
  with self.assertRaises(Refused): RecoveryContext(c.subject,"cut","1"*64,"2"*64,-1)
