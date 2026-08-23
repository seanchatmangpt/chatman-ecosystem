import unittest
from fractions import Fraction
from scripts.measure_train.validation_independence_realization_msa.graph import Evidence,admit_graph
from scripts.measure_train.validation_independence_realization_msa.validator import Validator
from scripts.measure_train.validation_independence_realization_msa.empirical import PairStats
from scripts.measure_train.validation_independence_realization_msa.calibration import Calibration
from scripts.measure_train.validation_independence_realization_msa.frontier import IndependenceModel
from scripts.measure_train.validation_independence_realization_msa.robustness import Robustness
from scripts.measure_train.validation_independence_realization_msa.admission import admit_independence
from scripts.measure_train.validation_independence_realization_msa.subject import Refused
from scripts.measure_train.validation_independence_realization_msa.standing import standing
class T(unittest.TestCase):
 def test_shared_ancestry_refuses_and_red_dominates(self):
  g=admit_graph([Evidence("r",(),0,"a"*64),Evidence("x",("r",),1,"b"*64),Evidence("y",("r",),1,"c"*64)])
  a=Validator("a","1"*64,"2"*64,"3"*64,"d1","x"); b=Validator("b","4"*64,"5"*64,"6"*64,"d2","y")
  cal=Calibration(10,Fraction(0),Fraction(0),Fraction(1),"CALIBRATED"); model=IndependenceModel(1,"7"*64,"CALIBRATED")
  with self.assertRaises(Refused): admit_independence(g,a,b,PairStats(10,0.25,0,0),cal,model)
  self.assertEqual(standing(cal,model,["BUILD_BROKEN"],False,Robustness(Fraction(0),Fraction(0),Fraction(0))),"BUILD_BROKEN")
