import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consumer_binding.subject import Subject
from scripts.measure_train.consumer_binding.producer import ProducerEvidence
from scripts.measure_train.consumer_binding.consumer import Consumer
from scripts.measure_train.consumer_binding.lease import EvidenceLease
from scripts.measure_train.consumer_binding.claim import ConsumptionClaim
from scripts.measure_train.consumer_binding.receipt import manufacture_receipt
class T(unittest.TestCase):
 def test_deterministic_no_do(self):
  now=datetime(2026,8,22,tzinfo=timezone.utc); p=ProducerEvidence(Subject("p/r","a"*40),"1"*64,"x","PARTIAL_ALIVE")
  c=ConsumptionClaim(Consumer(Subject("c/r","b"*40),"x"),p,EvidenceLease("1"*64,now,now+timedelta(hours=1)),"FOCUSED")
  a=manufacture_receipt(c,"CURRENT","ADMITTED"); b=manufacture_receipt(c,"CURRENT","ADMITTED")
  self.assertEqual(a,b); self.assertFalse(a["body"]["actuation_performed"])
