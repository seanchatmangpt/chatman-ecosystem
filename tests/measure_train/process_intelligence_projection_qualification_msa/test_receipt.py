import unittest
from scripts.measure_train.process_intelligence_projection_qualification_msa.subject import Subject
from scripts.measure_train.process_intelligence_projection_qualification_msa.receipt import manufacture
from scripts.measure_train.process_intelligence_projection_qualification_msa.replay import replay
from scripts.measure_train.process_intelligence_projection_qualification_msa.refusal import Refused
class T(unittest.TestCase):
    def test_tamper_refuses(self):
        r=manufacture(Subject('o/r','a'*40,'b'*64),(),'PARTIAL_ALIVE'); self.assertEqual(replay(r),'REPLAY_MATCH'); r['body']['standing']='ALIVE'
        with self.assertRaises(Refused): replay(r)
