import unittest
from scripts.measure_train.strategy_binding.subject import Subject,Refused
from scripts.measure_train.strategy_binding.proof import SelectionProof
class T(unittest.TestCase):
 def test_digest_contract(self):
  p=SelectionProof(Subject("c/r","a"*40),"cut","1"*64,"2"*64,"p"); self.assertEqual(p.proof_id,"p")
  with self.assertRaises(Refused): SelectionProof(p.consumer,"cut","x","2"*64,"p")
