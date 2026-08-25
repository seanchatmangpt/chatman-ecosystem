import unittest
from datetime import datetime,timezone
from scripts.measure_train.validation_independence_realization_msa.subject import Subject,Refused
from scripts.measure_train.validation_independence_realization_msa.trial import IndependenceTrial
from scripts.measure_train.validation_independence_realization_msa.calibration import calibrate
from scripts.measure_train.validation_independence_realization_msa.frontier import IndependenceModel,current
class T(unittest.TestCase):
 def test_false_independent_and_split_frontier(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  rows=[IndependenceTrial(s,str(i),"INDEPENDENT","DEPENDENT" if i==0 else "INDEPENDENT",now) for i in range(10)]
  self.assertEqual(calibrate(rows).state,"CALIBRATED")
  with self.assertRaises(Refused): current([IndependenceModel(2,"a"*64,"CALIBRATED"),IndependenceModel(2,"b"*64,"CALIBRATED")])
