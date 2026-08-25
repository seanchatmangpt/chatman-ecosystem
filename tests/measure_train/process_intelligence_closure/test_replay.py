import unittest
from scripts.measure_train.process_intelligence_closure.subject import Subject,Refused
from scripts.measure_train.process_intelligence_closure.receipt import manufacture
from scripts.measure_train.process_intelligence_closure.replay import replay

class T(unittest.TestCase):
    def test_tamper(self):
        census={"methodology_missing":(),"rail_states":{},"distributed":"CURRENT","obligations":()}
        r=manufacture(Subject("o/r","a"*40),census,"PARTIAL_ALIVE")
        self.assertEqual(replay(r),"REPLAY_MATCH")
        r["body"]["standing"]="ALIVE"
        with self.assertRaises(Refused): replay(r)
