import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.transport_invariance_realization_msa.subject import Subject
from scripts.measure_train.transport_invariance_realization_msa.stress import StressIdentity
from scripts.measure_train.transport_invariance_realization_msa.case import RealizationCase
from scripts.measure_train.transport_invariance_realization_msa.confusion import confusion
from scripts.measure_train.transport_invariance_realization_msa.estimators import LossMatrix,realized_loss,wilson_upper,hoeffding_radius,calibrate_risk
class T(unittest.TestCase):
 def test_confusion_loss_bounds_and_calibration(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); rows=[]
  for i,ok in enumerate([True,True,True,True,False]):
   st=StressIdentity(f"s{i}","TARGET_SHIFT",Fraction(i,10),1)
   rows.append(RealizationCase(s,st,True,Fraction(1 if ok else 3,10),ok,Fraction(1 if ok else 4,10),"CONFORMANCE","PLAN","us-a","r",f"c{i}",now))
  conf=confusion(rows); self.assertEqual(conf.false_stable,1); self.assertGreater(wilson_upper(1,5),0); self.assertGreater(hoeffding_radius(5),0)
  self.assertEqual(realized_loss(rows,LossMatrix(Fraction(3),Fraction(1))),Fraction(3,5))
  self.assertEqual(calibrate_risk(rows,min_support=5,max_mae=Fraction(1,5)).state,"CALIBRATED")
