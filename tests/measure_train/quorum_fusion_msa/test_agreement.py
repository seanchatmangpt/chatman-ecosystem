import unittest
from datetime import datetime,timezone
from scripts.measure_train.quorum_fusion_msa.subject import Subject
from scripts.measure_train.quorum_fusion_msa.sensor import Sensor
from scripts.measure_train.quorum_fusion_msa.trial import Trial
from scripts.measure_train.quorum_fusion_msa.agreement import pairwise_agreement
class T(unittest.TestCase):
 def test_pair(self):
  now=datetime.now(timezone.utc); subj=Subject("o/r","a"*40)
  a=Sensor(subj,"a","f1","d1",1,"1"*64); b=Sensor(subj,"b","f2","d2",1,"2"*64)
  rows=[Trial(a,"x","CURRENT","CURRENT",now),Trial(b,"x","CURRENT","CURRENT",now)]
  self.assertEqual(pairwise_agreement(rows)[('a','b')],1.0)
