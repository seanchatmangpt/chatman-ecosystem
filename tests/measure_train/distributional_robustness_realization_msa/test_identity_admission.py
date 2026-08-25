import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.distributional_robustness_realization_msa.subject import Subject
from scripts.measure_train.distributional_robustness_realization_msa.distribution import Distribution
from scripts.measure_train.distributional_robustness_realization_msa.ambiguity import AmbiguityModel
from scripts.measure_train.distributional_robustness_realization_msa.observation import RealizationObservation
from scripts.measure_train.distributional_robustness_realization_msa.admission import admit
from scripts.measure_train.distributional_robustness_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def test_exact_foreign_future(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64,1); d=Distribution((("x",Fraction(1)),)); m=AmbiguityModel("TV",Fraction(1,10),1,"c"*64)
  r=RealizationObservation(s,"e",m,d,Fraction(1,10),Fraction(1,5),Fraction(1,5),"DISCOVERY","e","r","root",now)
  self.assertEqual(admit(s,[r],now),(r,))
  foreign=Subject("o/r","d"*40,"b"*64,1)
  with self.assertRaisesRegex(Refused,"FOREIGN_OR_STALE_SUBJECT"): admit(s,[RealizationObservation(foreign,"x",m,d,Fraction(0),Fraction(0),Fraction(0),"DISCOVERY","e","r","root",now)],now)
  with self.assertRaisesRegex(Refused,"FUTURE_OBSERVATION"): admit(s,[RealizationObservation(s,"f",m,d,Fraction(0),Fraction(0),Fraction(0),"DISCOVERY","e","r","root",now+timedelta(seconds=1))],now)
