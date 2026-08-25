import unittest
from scripts.measure_train.quorum_fusion_msa.distribution import jensen_shannon
class T(unittest.TestCase):
 def test_js_identity(self):
  p=(.1,.1,.1,.7)
  self.assertAlmostEqual(jensen_shannon(p,p),0.0)
