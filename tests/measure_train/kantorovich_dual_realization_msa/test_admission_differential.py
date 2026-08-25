import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.kantorovich_dual_realization_msa.subject import Subject
from scripts.measure_train.kantorovich_dual_realization_msa.certificate import Certificate
from scripts.measure_train.kantorovich_dual_realization_msa.observation import CertificateObservation
from scripts.measure_train.kantorovich_dual_realization_msa.admission import admit
from scripts.measure_train.kantorovich_dual_realization_msa.differential import oracle_differential
from scripts.measure_train.kantorovich_dual_realization_msa.errors import Refused
class T(unittest.TestCase):
 def test_foreign_future_and_exact_oracle(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc); c=Certificate(Fraction(1,2),Fraction(1,2),Fraction(0),Fraction(0),"c"*64,"d"*64)
  r=CertificateObservation(s,"x",c,Fraction(1,2),Fraction(1,2),"i","m",now)
  self.assertEqual(oracle_differential(admit(s,[r],now)).mae,0)
  with self.assertRaises(Refused): admit(s,[CertificateObservation(s,"y",c,Fraction(1,2),Fraction(1,2),"i","m",now+timedelta(seconds=1))],now)
