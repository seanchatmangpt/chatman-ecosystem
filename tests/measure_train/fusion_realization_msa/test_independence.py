import unittest
from scripts.measure_train.fusion_realization_msa.sensor import SensorIdentity
from scripts.measure_train.fusion_realization_msa.independence import IndependenceProof,admit_independence
from scripts.measure_train.fusion_realization_msa.subject import Refused
class T(unittest.TestCase):
 def test_shared_runtime_refuses(self):
  a=SensorIdentity("a","fa","rt","1"*64,"a"*64); b=SensorIdentity("b","fb","rt","2"*64,"b"*64)
  p=IndependenceProof("a","b","f"*64,.1)
  with self.assertRaises(Refused): admit_independence(a,b,p)
