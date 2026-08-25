import unittest
from fractions import Fraction
from scripts.measure_train.dependence_structure_msa.subject import Refused
from scripts.measure_train.dependence_structure_msa.provenance import ProvenanceClaim,audit
from scripts.measure_train.dependence_structure_msa.frontier import DependenceModel,current_frontier
from scripts.measure_train.dependence_structure_msa.calibration import Calibration
from scripts.measure_train.dependence_structure_msa.composition_policy import composition_mode
class T(unittest.TestCase):
 def test_empirical_contradiction_and_current_policy(self):
  c=ProvenanceClaim("L","R",True,True,True,True)
  with self.assertRaises(Refused): audit(c,"DEPENDENT")
  m=DependenceModel("L|R",2,"a"*64,"CALIBRATED")
  self.assertEqual(current_frontier([DependenceModel("L|R",1,"b"*64,"CALIBRATED"),m])[0],m)
  cal=Calibration(10,Fraction(0),Fraction(0),"CALIBRATED")
  self.assertEqual(composition_mode("INDEPENDENT",cal,m,audit(c,"INDEPENDENT")),"INDEPENDENT")
