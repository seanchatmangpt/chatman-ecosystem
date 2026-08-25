import unittest
from datetime import datetime,timezone
from scripts.measure_train.quorum_fusion_msa.subject import Subject
from scripts.measure_train.quorum_fusion_msa.sensor import Sensor
from scripts.measure_train.quorum_fusion_msa.trial import Trial
from scripts.measure_train.quorum_fusion_msa.calibration import calibrate
class T(unittest.TestCase):
 def test_support(self):
  s=Sensor(Subject("o/r","a"*40),"s","f","d",1,"1"*64); now=datetime.now(timezone.utc)
  rows=[Trial(s,str(i),"CURRENT","CURRENT",now) for i in range(5)]
  self.assertEqual(calibrate(s,rows).support,5)
