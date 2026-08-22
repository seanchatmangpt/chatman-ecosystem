import unittest
from fractions import Fraction
from datetime import datetime,timezone
from scripts.measure_train.evidence_voi.belief import BeliefState
from scripts.measure_train.evidence_voi.candidate import MeasurementCandidate
from scripts.measure_train.evidence_voi.calibration import SensorCalibration
from scripts.measure_train.evidence_voi.budget import AcquisitionBudget
from scripts.measure_train.evidence_voi.dependence import IndependenceProof
from scripts.measure_train.evidence_voi.selector import select_measurements
class T(unittest.TestCase):
 def test_useful_independent_measurements_selected(self):
  now=datetime.now(timezone.utc); b=BeliefState(Fraction(1,2),0)
  a=MeasurementCandidate("a","f1","d1","REPOSITORY",Fraction(1),10); c=MeasurementCandidate("c","f2","d2","RUNTIME",Fraction(1),20)
  ca=SensorCalibration("a",1,10,Fraction(9,10),Fraction(1,10),now); cc=SensorCalibration("c",1,10,Fraction(4,5),Fraction(1,5),now)
  selected=select_measurements(b,[a,c],[ca,cc],AcquisitionBudget(Fraction(3),100,2),[IndependenceProof("a","c","separate domains")])
  self.assertEqual({x.candidate_id for x in selected},{"a","c"})
