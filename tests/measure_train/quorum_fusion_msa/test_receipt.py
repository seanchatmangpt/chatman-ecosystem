import unittest
from scripts.measure_train.quorum_fusion_msa.subject import Subject
from scripts.measure_train.quorum_fusion_msa.sensor import Sensor
from scripts.measure_train.quorum_fusion_msa.receipt import manufacture_receipt
from scripts.measure_train.quorum_fusion_msa.replay import replay
class T(unittest.TestCase):
 def test_tamper(self):
  sub=Subject("o/r","a"*40); s=Sensor(sub,"s","f","d",1,"1"*64)
  r=manufacture_receipt(sub,[s],{"state":"COHERENT","center":(0,0,0,1)},{"score":1.0,"pairs":()},"PARTIAL_ALIVE")
  self.assertEqual(replay(r),"REPLAY_MATCH")
  r["body"]["standing"]="ALIVE"
  with self.assertRaises(Exception): replay(r)
