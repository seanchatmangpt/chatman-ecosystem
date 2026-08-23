import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.manifest_reference_observability_msa.component import ComponentRef
from scripts.measure_train.manifest_reference_observability_msa.transport import TransportIdentity
from scripts.measure_train.manifest_reference_observability_msa.observation import RefObservation
from scripts.measure_train.manifest_reference_observability_msa.admission import admit_observations
from scripts.measure_train.manifest_reference_observability_msa.refusal import Refused

class T(unittest.TestCase):
 def test_foreign_future_and_censored_shape_refuse(self):
  now=datetime.now(timezone.utc)
  c=ComponentRef("p","o/p","main","a"*40)
  t=TransportIdentity("github-api",1,"b"*64,"c"*64,"api.github.com")
  good=RefObservation("p",t,"RESOLVED",now,10,"a"*40,"EXACT","e1")
  self.assertEqual(len(admit_observations([c],[good],now)),1)
  with self.assertRaises(Refused):
   admit_observations([c],[RefObservation("p",t,"RESOLVED",now+timedelta(seconds=1),10,"a"*40,"EXACT","e2")],now)
  with self.assertRaises(Refused):
   RefObservation("p",t,"TIMEOUT",now,1000,"a"*40,"UNKNOWN","e3")
