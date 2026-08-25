import unittest
from scripts.measure_train.kantorovich_dual_realization_msa.frontier import CalibrationModel,current
from scripts.measure_train.kantorovich_dual_realization_msa.methodology import REQUIRED,require
from scripts.measure_train.kantorovich_dual_realization_msa.errors import Refused
class T(unittest.TestCase):
 def test_current_and_methods(self):
  self.assertEqual(current([CalibrationModel(1,"a"*64,"CALIBRATED"),CalibrationModel(2,"b"*64,"CALIBRATED")]).generation,2); self.assertTrue(require(REQUIRED))
  with self.assertRaises(Refused): current([CalibrationModel(2,"a"*64,"CALIBRATED"),CalibrationModel(2,"b"*64,"CALIBRATED")])
