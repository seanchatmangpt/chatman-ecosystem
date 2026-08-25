import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.distributional_robustness_realization_msa.ambiguity import AmbiguityModel
from scripts.measure_train.distributional_robustness_realization_msa.frontier import current_models
from scripts.measure_train.distributional_robustness_realization_msa.drift import cusum
from scripts.measure_train.distributional_robustness_realization_msa.subject import Subject
from scripts.measure_train.distributional_robustness_realization_msa.distribution import Distribution
from scripts.measure_train.distributional_robustness_realization_msa.observation import RealizationObservation
from scripts.measure_train.distributional_robustness_realization_msa.strata import worst_stratum
from scripts.measure_train.distributional_robustness_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def test_currentness_drift_worst(self):
  a=AmbiguityModel("TV",Fraction(1,10),1,"a"*64); b=AmbiguityModel("TV",Fraction(2,10),2,"b"*64); self.assertEqual(current_models([a,b]),(b,))
  with self.assertRaisesRegex(Refused,"DIVERGENT_CURRENT"): current_models([b,AmbiguityModel("TV",Fraction(2,10),2,"c"*64)])
  self.assertTrue(cusum([0.1,0.2,0.5],0.1,0.0,0.4).drifted)
  now=datetime.now(timezone.utc); s=Subject("o/r","d"*40,"e"*64,1); d=Distribution((("x",Fraction(1)),))
  rows=[RealizationObservation(s,"a",b,d,Fraction(1),Fraction(0),Fraction(0),"DISCOVERY","e1","r","z",now),RealizationObservation(s,"b",b,d,Fraction(0),Fraction(1),Fraction(1),"CONFORMANCE","e2","r","z",now)]
  self.assertEqual(worst_stratum(rows)[1].methodology,"DISCOVERY")
