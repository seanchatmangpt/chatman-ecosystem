import unittest, copy
from scripts.release_train.invalidation_promotion.receipt import manufacture_receipt, replay_receipt
from scripts.release_train.invalidation_promotion.subject import Refusal
class T(unittest.TestCase):
 def test_determinism_and_tamper(self):
  a=manufacture_receipt({'x':1}); b=manufacture_receipt({'x':1})
  self.assertEqual(a,b); self.assertTrue(replay_receipt(a))
  c=copy.deepcopy(a); c['body']['payload']['x']=2
  with self.assertRaises(Refusal): replay_receipt(c)
