import unittest
from scripts.measure_train.quorum_fusion_msa.subject import Subject
from scripts.measure_train.quorum_fusion_msa.sensor import Sensor
from scripts.measure_train.quorum_fusion_msa.independence import IndependenceProof,independent_pairs
class T(unittest.TestCase):
 def test_proof_required(self):
  sub=Subject("o/r","a"*40); a=Sensor(sub,"a","f1","d1",1,"1"*64); b=Sensor(sub,"b","f2","d2",1,"2"*64)
  self.assertEqual(independent_pairs([a,b],[]),set())
  self.assertEqual(independent_pairs([a,b],[IndependenceProof("a","b","p")]),{("a","b")})
