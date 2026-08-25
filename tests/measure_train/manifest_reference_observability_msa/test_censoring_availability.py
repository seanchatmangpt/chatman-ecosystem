import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.manifest_reference_observability_msa.transport import TransportIdentity
from scripts.measure_train.manifest_reference_observability_msa.observation import RefObservation
from scripts.measure_train.manifest_reference_observability_msa.censoring import resolution_survival
from scripts.measure_train.manifest_reference_observability_msa.availability import estimate
from scripts.measure_train.manifest_reference_observability_msa.hazard import measure

class T(unittest.TestCase):
 def test_timeout_is_censoring_not_semantic_divergence(self):
  now=datetime.now(timezone.utc); t=TransportIdentity("api",1,"a"*64,"b"*64,"github")
  rows=[
   RefObservation("x",t,"RESOLVED",now,100,"c"*40,"EXACT","1"),
   RefObservation("x",t,"TIMEOUT",now,1000,None,"UNKNOWN","2"),
   RefObservation("x",t,"TIMEOUT",now,1000,None,"UNKNOWN","3"),
  ]
  curve=resolution_survival(rows); self.assertTrue(curve)
  self.assertEqual(estimate(rows).resolved,1)
  self.assertEqual(measure(rows).timeout_rate,Fraction(2,3))
