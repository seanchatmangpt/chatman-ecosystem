import unittest
from scripts.measure_train.cross_control_msa.search import admit_search
from scripts.measure_train.cross_control_msa.semantic import admit_semantic
from scripts.measure_train.cross_control_msa.distributed import admit_distributed
from scripts.measure_train.cross_control_msa.simulation import admit_simulation
from scripts.measure_train.cross_control_msa.refusal import Refused
class T(unittest.TestCase):
 def test_controls(self):
  self.assertTrue(admit_search(2,3,1,5,5,2,.1)); self.assertTrue(admit_semantic(True,True,True,0,0)); self.assertTrue(admit_distributed(True,"concurrent",3,2,"closed","a"*64)); self.assertTrue(admit_simulation(.1,2,True,False,True,True))
  with self.assertRaises(Refused): admit_search(6,3,1,5,5,2,.1)
