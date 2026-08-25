import unittest
from scripts.measure_train.supersession.subject import Subject, Refused
from scripts.measure_train.supersession.receipt import manufacture_receipt
from scripts.measure_train.supersession.replay import replay

class TestReplay(unittest.TestCase):
    def test_tamper_refuses(self):
        r=manufacture_receipt(Subject("o/r","a"*40),[],[],"UNKNOWN")
        self.assertEqual(replay(r),"REPLAY_MATCH")
        r["body"]["sha"]="b"*40
        with self.assertRaises(Refused):
            replay(r)
