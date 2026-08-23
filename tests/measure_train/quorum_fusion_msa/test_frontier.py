import unittest
from scripts.measure_train.quorum_fusion_msa.subject import Subject,Refused
from scripts.measure_train.quorum_fusion_msa.sensor import Sensor
from scripts.measure_train.quorum_fusion_msa.frontier import current_frontier
class T(unittest.TestCase):
 def test_divergence(self):
  sub=Subject("o/r","a"*40); a=Sensor(sub,"s","f","d",1,"1"*64); b=Sensor(sub,"s","f","d",1,"2"*64)
  with self.assertRaises(Refused): current_frontier([a,b])
