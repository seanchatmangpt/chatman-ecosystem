import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.kantorovich_dual_realization_msa.subject import Subject
from scripts.measure_train.kantorovich_dual_realization_msa.certificate import Certificate
from scripts.measure_train.kantorovich_dual_realization_msa.observation import CertificateObservation
from scripts.measure_train.kantorovich_dual_realization_msa.qualify import qualify
from scripts.measure_train.kantorovich_dual_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_full_realization_ceiling_and_red_dependency(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc); rows=[]
  for i in range(3):
   c=Certificate(Fraction(1,2),Fraction(1,2),Fraction(0),Fraction(0),("c"*63)+str(i),"d"*64)
   rows.append(CertificateObservation(s,str(i),c,Fraction(1,2),Fraction(1,2),"impl","model",now))
  q=qualify(s,rows,now); self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  q2=qualify(s,rows,now,["BUILD_BROKEN"]); self.assertEqual(q2["standing"],"BUILD_BROKEN"); self.assertIsNone(q2["receipt"])
