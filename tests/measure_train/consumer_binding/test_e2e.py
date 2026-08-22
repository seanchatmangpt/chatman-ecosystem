import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consumer_binding.subject import Subject
from scripts.measure_train.consumer_binding.producer import ProducerEvidence
from scripts.measure_train.consumer_binding.consumer import Consumer
from scripts.measure_train.consumer_binding.lease import EvidenceLease
from scripts.measure_train.consumer_binding.claim import ConsumptionClaim
from scripts.measure_train.consumer_binding.qualify import qualify
from scripts.measure_train.consumer_binding.replay import replay
class T(unittest.TestCase):
 def test_current_binding_and_no_do(self):
  now=datetime.now(timezone.utc); p=ProducerEvidence(Subject("p/r","a"*40),"1"*64,"schema/1","PARTIAL_ALIVE")
  c=ConsumptionClaim(Consumer(Subject("c/r","b"*40),"release"),p,EvidenceLease("1"*64,now-timedelta(seconds=1),now+timedelta(hours=1)),"REPOSITORY")
  q=qualify(c,p,"REPOSITORY",now)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertEqual(q["drift"],"CURRENT")
  self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
