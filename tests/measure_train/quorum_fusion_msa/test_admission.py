import unittest
from scripts.measure_train.quorum_fusion_msa.subject import Subject,Refused
from scripts.measure_train.quorum_fusion_msa.sensor import Sensor
from scripts.measure_train.quorum_fusion_msa.calibration import Calibration
from scripts.measure_train.quorum_fusion_msa.admission import admit
class T(unittest.TestCase):
 def test_false_current_refuses(self):
  s=Sensor(Subject("o/r","a"*40),"s","f","d",1,"1"*64)
  with self.assertRaises(Refused): admit([s],[Calibration("s",1,10,.3,.0,.0)],[s])
