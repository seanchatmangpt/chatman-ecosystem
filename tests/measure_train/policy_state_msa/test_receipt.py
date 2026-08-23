import unittest
from scripts.measure_train.policy_state_msa.subject import Subject,Refused
from scripts.measure_train.policy_state_msa.receipt import manufacture_receipt
from scripts.measure_train.policy_state_msa.replay import replay
class T(unittest.TestCase):
    def test_tamper_refuses(self):
        r=manufacture_receipt(Subject("o/r","a"*40),None,{"standing":"UNKNOWN"}); self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["actuation_performed"]=True
        with self.assertRaises(Refused): replay(r)
