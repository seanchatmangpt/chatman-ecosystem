import unittest
from scripts.measure_train.process_trace_relation_msa.subject import Subject
from scripts.measure_train.process_trace_relation_msa.relation import Relation
from scripts.measure_train.process_trace_relation_msa.calibration import RelationCalibration
from scripts.measure_train.process_trace_relation_msa.receipt_replay_qualify import qualify,replay
class T(unittest.TestCase):
 def test_chicago_positive_ceiling_and_red_dependency(self):
  s=Subject("seanchatmangpt/chatman-ecosystem","a"*40,"b"*64)
  cs=[RelationCalibration(r,12,1,1,0,0.7,"CALIBRATED") for r in Relation]
  q=qualify(s,cs,(("identity",4),("stutter",4),("commute",4)))
  self.assertEqual(q["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q["actuation_performed"])
  self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  self.assertEqual(qualify(s,cs,(),["BUILD_BROKEN"])["standing"],"BUILD_BROKEN")
