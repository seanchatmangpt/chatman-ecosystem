import unittest
from scripts.measure_train.quorum_fusion_msa.subject import Refused
from scripts.measure_train.quorum_fusion_msa.calibration import Calibration
from scripts.measure_train.quorum_fusion_msa.consensus import consensus
class T(unittest.TestCase):
 def test_independence_required(self):
  rows=[Calibration("a",1,10,.01,.01,.01),Calibration("b",1,10,.01,.01,.01)]
  with self.assertRaises(Refused): consensus(rows,set())
  self.assertGreater(consensus(rows,{("a","b")})["score"],.9)
