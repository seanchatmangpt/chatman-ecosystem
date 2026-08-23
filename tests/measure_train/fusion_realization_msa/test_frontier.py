import unittest
from scripts.measure_train.fusion_realization_msa.frontier import CalibrationFrontier,current_frontier
from scripts.measure_train.fusion_realization_msa.subject import Refused
class T(unittest.TestCase):
 def test_divergent_latest_refuses(self):
  rows=[CalibrationFrontier("p",2,"1"*64),CalibrationFrontier("p",2,"2"*64)]
  with self.assertRaises(Refused): current_frontier(rows)
