import unittest
from scripts.measure_train.acquisition_realization.subject import Subject,Refused
from scripts.measure_train.acquisition_realization.receipt import manufacture_receipt
from scripts.measure_train.acquisition_realization.replay import replay
class T(unittest.TestCase):
 def test_deterministic_tamper_no_do(self):
  s=Subject("o/r","a"*40); a=manufacture_receipt(s,1,"1"*64,(),"UNKNOWN"); b=manufacture_receipt(s,1,"1"*64,(),"UNKNOWN")
  self.assertEqual(a,b); self.assertEqual(replay(a),"REPLAY_MATCH")
  a["body"]["actuation_performed"]=True
  with self.assertRaises(Refused): replay(a)
