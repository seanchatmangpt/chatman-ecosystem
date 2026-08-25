import unittest
from scripts.measure_train.delta.identity_delta import HeadDelta
from scripts.measure_train.delta.ci_vector import CIVector
from scripts.measure_train.delta.movement import Movement
from scripts.measure_train.delta.receipt_chain import manufacture,replay
from scripts.measure_train.delta.qualify import qualify
class T(unittest.TestCase):
 def test_delta_pipeline_is_deterministic_non_actuating(self):
  h=HeadDelta('o/r','a'*40,'b'*40); before=CIVector.from_mapping({'court':'PASS'}); after=CIVector.from_mapping({'court':'FAIL'})
  m=Movement(h.moved,True,bool(before.transition(after)),False)
  standing=qualify(movement_material=m.material,ci_outcomes=['FAIL'],runtime_standing='UNKNOWN',stale=False,contradictions_rows=[])
  body,d=manufacture({'standing':standing,'dims':m.dimensions},None); self.assertEqual(standing,'BUILD_BROKEN'); self.assertTrue(replay(body,d)); self.assertFalse(body['actuation_performed'])
