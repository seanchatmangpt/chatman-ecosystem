import unittest
from scripts.measure_train.federation_epistemic_capital_msa.frontier import CapitalModel,current
from scripts.measure_train.federation_epistemic_capital_msa.methodology import REQUIRED,require_complete
from scripts.measure_train.federation_epistemic_capital_msa.refusal import Refused
class T(unittest.TestCase):
 def test_split_and_incomplete_refuse(self):
  with self.assertRaises(Refused): current([CapitalModel("m",1,"a"*64,"CALIBRATED"),CapitalModel("m",1,"b"*64,"CALIBRATED")])
  with self.assertRaises(Refused): require_complete(REQUIRED-{"INTERVENTION"})
