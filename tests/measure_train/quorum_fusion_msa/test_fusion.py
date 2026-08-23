import unittest
from scripts.measure_train.quorum_fusion_msa.calibration import Calibration
from scripts.measure_train.quorum_fusion_msa.fusion import fuse
class T(unittest.TestCase):
 def test_coherent(self):
  rows=[Calibration("a",1,10,.02,.03,.01),Calibration("b",1,10,.03,.02,.01)]
  self.assertEqual(fuse(rows)["state"],"COHERENT")
