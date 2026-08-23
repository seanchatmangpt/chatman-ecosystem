import unittest
from scripts.measure_train.process_trace_relation_msa.subject import Subject,Refused
from scripts.measure_train.process_trace_relation_msa.relation import Relation
from scripts.measure_train.process_trace_relation_msa.calibration import RelationCalibration
from scripts.measure_train.process_trace_relation_msa.receipt_replay_qualify import manufacture,replay
class T(unittest.TestCase):
 def test_replay(self):
  s=Subject("o/r","a"*40,"b"*64)
  cs=[RelationCalibration(r,10,1,1,0,0.7,"CALIBRATED") for r in Relation]
  receipt=manufacture(s,cs,(("identity",4),))
  self.assertEqual(replay(receipt),"REPLAY_MATCH")
  receipt["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(receipt)
