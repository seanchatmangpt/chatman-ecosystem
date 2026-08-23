import unittest
from datetime import datetime,timezone
from scripts.measure_train.dependence_structure_msa.subject import Subject
from scripts.measure_train.dependence_structure_msa.observation import PairObservation
from scripts.measure_train.dependence_structure_msa.exact_test import exact_permutation_p_value
from scripts.measure_train.dependence_structure_msa.calibration import LabeledVerdict,calibrate
class T(unittest.TestCase):
 def test_permutation_and_calibration(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  rows=[PairObservation(s,"L","R",str(i),v,v,"all",now) for i,v in enumerate([0,1]*4)]
  self.assertLessEqual(exact_permutation_p_value(rows),0.05)
  labels=[LabeledVerdict("INDEPENDENT","INDEPENDENT") for _ in range(3)]+[LabeledVerdict("DEPENDENT","DEPENDENT") for _ in range(3)]
  self.assertEqual(calibrate(labels).state,"CALIBRATED")
