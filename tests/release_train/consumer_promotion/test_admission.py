import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.consumer_promotion.subject import Subject
from scripts.release_train.consumer_promotion.evidence import ProducerEvidence
from scripts.release_train.consumer_promotion.lease import EvidenceLease
from scripts.release_train.consumer_promotion.claim import ConsumptionClaim
from scripts.release_train.consumer_promotion.admission import admit
class T(unittest.TestCase):
 def test_superseded_refuses(self):
  s=Subject("o/r","a"*40); c=Subject("o/c","b"*40); now=datetime.now(timezone.utc); l=EvidenceLease(now-timedelta(minutes=1),now+timedelta(minutes=1))
  e=ProducerEvidence(s,"1"*64,"v1","ALIVE","REPOSITORY"); q=ConsumptionClaim(c,s,"x","1"*64,"v1","REPOSITORY",l)
  self.assertIn("SUPERSEDED",admit(q,e,"2"*64,"v1",now).reason)
