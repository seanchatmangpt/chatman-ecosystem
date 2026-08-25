import unittest
from datetime import datetime,timezone
from scripts.measure_train.manifest_reference_observability_msa.subject import Subject
from scripts.measure_train.manifest_reference_observability_msa.component import ComponentRef
from scripts.measure_train.manifest_reference_observability_msa.transport import TransportIdentity
from scripts.measure_train.manifest_reference_observability_msa.observation import RefObservation
from scripts.measure_train.manifest_reference_observability_msa.qualify import qualify
from scripts.measure_train.manifest_reference_observability_msa.replay import replay

class T(unittest.TestCase):
 def test_live_shape_11_timeouts_is_blocked_not_semantic_divergence(self):
  now=datetime.now(timezone.utc); subject=Subject("seanchatmangpt/chatman-ecosystem","9"*40)
  components=[ComponentRef(f"c{i}","o/r","main","a"*40) for i in range(16)]
  t=TransportIdentity("release-ref-api",1,"b"*64,"c"*64,"github-ref-check")
  obs=[]
  for i,c in enumerate(components):
   if i<5:
    obs.append(RefObservation(c.component_id,t,"RESOLVED",now,50,c.expected_sha,"EXACT",f"e{i}"))
   else:
    obs.append(RefObservation(c.component_id,t,"TIMEOUT",now,120000,None,"UNKNOWN",f"e{i}"))
  q=qualify(subject,components,obs,[],now)
  self.assertEqual(q["standing"],"BLOCKED")
  self.assertEqual(q["coverage"].exact,5)
  self.assertEqual(q["coverage"].censored,11)
  self.assertIsNone(q["receipt"])

 def test_all_exact_is_only_partial_alive_and_replayable(self):
  now=datetime.now(timezone.utc); subject=Subject("seanchatmangpt/chatman-ecosystem","9"*40)
  components=[ComponentRef(f"c{i}","o/r","main","a"*40) for i in range(4)]
  t=TransportIdentity("release-ref-api",2,"b"*64,"c"*64,"github-ref-check")
  obs=[RefObservation(c.component_id,t,"RESOLVED",now,30,c.expected_sha,"EXACT",f"e{i}") for i,c in enumerate(components)]
  q=qualify(subject,components,obs,[],now)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q["actuation_performed"])
  self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
