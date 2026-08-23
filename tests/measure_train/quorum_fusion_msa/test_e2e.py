import unittest
from scripts.measure_train.quorum_fusion_msa.subject import Subject
from scripts.measure_train.quorum_fusion_msa.sensor import Sensor
from scripts.measure_train.quorum_fusion_msa.calibration import Calibration
from scripts.measure_train.quorum_fusion_msa.qualify import qualify
from scripts.measure_train.quorum_fusion_msa.replay import replay
class T(unittest.TestCase):
 def test_independent_coherent_fusion_bounded(self):
  sub=Subject("o/r","a"*40)
  a=Sensor(sub,"a","fam1","dom1",1,"1"*64); b=Sensor(sub,"b","fam2","dom2",1,"2"*64)
  rows=[Calibration("a",1,20,.02,.02,.01),Calibration("b",1,20,.03,.01,.01)]
  q=qualify(sub,[a,b],rows,{("a","b")})
  self.assertEqual(q["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q["actuation_performed"])
  self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
