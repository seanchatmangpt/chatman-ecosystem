import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consumer_binding.subject import Subject,Refused
from scripts.measure_train.consumer_binding.producer import ProducerEvidence
from scripts.measure_train.consumer_binding.consumer import Consumer
from scripts.measure_train.consumer_binding.lease import EvidenceLease
from scripts.measure_train.consumer_binding.claim import ConsumptionClaim
from scripts.measure_train.consumer_binding.admission import admit_claim
class T(unittest.TestCase):
 def test_superseded_refuses(self):
  now=datetime.now(timezone.utc); s=Subject("p/r","a"*40); c=Consumer(Subject("c/r","b"*40),"x")
  old=ProducerEvidence(s,"1"*64,"schema/1","PARTIAL_ALIVE"); new=ProducerEvidence(s,"2"*64,"schema/1","PARTIAL_ALIVE")
  claim=ConsumptionClaim(c,old,EvidenceLease("1"*64,now-timedelta(seconds=1),now+timedelta(seconds=10)),"FOCUSED")
  with self.assertRaises(Refused): admit_claim(claim,new,"REPOSITORY",now)
