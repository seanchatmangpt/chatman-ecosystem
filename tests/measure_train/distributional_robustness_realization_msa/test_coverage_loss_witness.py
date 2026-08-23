import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.distributional_robustness_realization_msa.subject import Subject
from scripts.measure_train.distributional_robustness_realization_msa.distribution import Distribution
from scripts.measure_train.distributional_robustness_realization_msa.ambiguity import AmbiguityModel
from scripts.measure_train.distributional_robustness_realization_msa.observation import RealizationObservation
from scripts.measure_train.distributional_robustness_realization_msa.coverage import empirical_coverage
from scripts.measure_train.distributional_robustness_realization_msa.loss import calibrate_loss
from scripts.measure_train.distributional_robustness_realization_msa.witness import calibrate_witness
from scripts.measure_train.distributional_robustness_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def rows(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64,1); d=Distribution((("x",Fraction(1)),)); m=AmbiguityModel("TV",Fraction(1,10),1,"c"*64)
  return [RealizationObservation(s,str(i),m,d,Fraction(i,10),Fraction(3,10),Fraction(3,10),"DISCOVERY","e","r","root",now) for i in range(5)]
 def test_calibration(self):
  rows=self.rows(); cov=empirical_coverage(rows,lambda r:r.realized_loss<=r.predicted_worst_loss); self.assertEqual((cov.support,cov.misses),(5,1)); self.assertEqual(calibrate_loss(rows).false_safe,1); self.assertEqual(calibrate_witness(rows).support,5)
  row=rows[0]; missing=RealizationObservation(row.subject,row.observation_id,row.model,row.target,row.realized_loss,row.predicted_worst_loss,None,row.methodology,row.engine,row.region,row.evidence_root,row.observed_at)
  with self.assertRaisesRegex(Refused,"UNOBSERVED_WORST_WITNESS"): calibrate_witness([missing])
