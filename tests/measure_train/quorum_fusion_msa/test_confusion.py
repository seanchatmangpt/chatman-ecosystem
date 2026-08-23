import unittest
from datetime import datetime,timezone
from scripts.measure_train.quorum_fusion_msa.subject import Subject
from scripts.measure_train.quorum_fusion_msa.sensor import Sensor
from scripts.measure_train.quorum_fusion_msa.trial import Trial
from scripts.measure_train.quorum_fusion_msa.confusion import confusion
class T(unittest.TestCase):
 def test_counts(self):
  s=Sensor(Subject("o/r","a"*40),"s","f","d",1,"1"*64); now=datetime.now(timezone.utc)
  c=confusion([Trial(s,"1","CURRENT","CURRENT",now),Trial(s,"2","STALE","STALE",now)])
  self.assertEqual((c.tp,c.tn),(1,1))
