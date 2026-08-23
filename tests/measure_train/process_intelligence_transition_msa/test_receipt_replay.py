import unittest
from scripts.measure_train.process_intelligence_transition_msa.subject import Subject,SubjectEpoch,Refused
from scripts.measure_train.process_intelligence_transition_msa.receipt import manufacture_receipt
from scripts.measure_train.process_intelligence_transition_msa.replay import replay

class T(unittest.TestCase):
    def test_tamper_refuses(self):
        e=SubjectEpoch(Subject("o/r","a"*40),1)
        r=manufacture_receipt(e,(("ci","CI",True,"PASS"),),(),(),"PARTIAL_ALIVE")
        self.assertEqual(replay(r),"REPLAY_MATCH")
        r["body"]["standing"]="ALIVE"
        with self.assertRaises(Refused):
            replay(r)
