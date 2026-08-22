import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consumer_binding.subject import Subject
from scripts.measure_train.consumer_binding.producer import ProducerEvidence
from scripts.measure_train.consumer_binding.consumer import Consumer
from scripts.measure_train.consumer_binding.lease import EvidenceLease
from scripts.measure_train.consumer_binding.claim import ConsumptionClaim
from scripts.measure_train.consumer_binding.drift import classify_drift
class T(unittest.TestCase):
 def test_receipt_drift(self):
  now=datetime.now(timezone.utc); s=Subject("p/r","a"*40)
  old=ProducerEvidence(s,"1"*64,"x","PARTIAL_ALIVE"); new=ProducerEvidence(s,"2"*64,"x","PARTIAL_ALIVE")
  claim=ConsumptionClaim(Consumer(Subject("c/r","b"*40),"x"),old,EvidenceLease("1"*64,now-timedelta(seconds=1),now+timedelta(seconds=1)),"FOCUSED")
  self.assertEqual(classify_drift(claim,new,now),"SUPERSEDED_RECEIPT")
