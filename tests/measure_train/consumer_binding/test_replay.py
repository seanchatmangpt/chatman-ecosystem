import unittest
from scripts.measure_train.consumer_binding.subject import Subject,Refused
from scripts.measure_train.consumer_binding.producer import ProducerEvidence
from scripts.measure_train.consumer_binding.consumer import Consumer
from scripts.measure_train.consumer_binding.lease import EvidenceLease
from scripts.measure_train.consumer_binding.claim import ConsumptionClaim
from scripts.measure_train.consumer_binding.receipt import manufacture_receipt
from scripts.measure_train.consumer_binding.replay import replay
from datetime import datetime,timezone,timedelta
class T(unittest.TestCase):
 def test_tamper(self):
  now=datetime.now(timezone.utc); p=ProducerEvidence(Subject("p/r","a"*40),"1"*64,"x","PARTIAL_ALIVE")
  c=ConsumptionClaim(Consumer(Subject("c/r","b"*40),"x"),p,EvidenceLease("1"*64,now,now+timedelta(hours=1)),"FOCUSED")
  r=manufacture_receipt(c,"CURRENT","ADMITTED"); self.assertEqual(replay(r),"REPLAY_MATCH")
  r["body"]["consumer_sha"]="c"*40
  with self.assertRaises(Refused): replay(r)
