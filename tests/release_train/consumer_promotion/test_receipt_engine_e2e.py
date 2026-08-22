import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.consumer_promotion.subject import Subject
from scripts.release_train.consumer_promotion.evidence import ProducerEvidence
from scripts.release_train.consumer_promotion.lease import EvidenceLease
from scripts.release_train.consumer_promotion.claim import ConsumptionClaim
from scripts.release_train.consumer_promotion.candidate import Candidate
from scripts.release_train.consumer_promotion.engine import manufacture_plan
from scripts.release_train.consumer_promotion.receipt import replay,Receipt
class T(unittest.TestCase):
 def test_e2e_and_tamper(self):
  p=Subject("o/p","a"*40); c=Subject("o/c","b"*40); now=datetime(2026,8,22,11,tzinfo=timezone.utc); lease=EvidenceLease(now-timedelta(minutes=10),now+timedelta(minutes=10))
  ev=ProducerEvidence(p,"1"*64,"schema1","ALIVE","REPOSITORY"); cl=ConsumptionClaim(c,p,"runtime","1"*64,"schema1","REPOSITORY",lease)
  plan,r=manufacture_plan(claim=cl,evidence=ev,current_receipt="1"*64,current_schema="schema1",now=now,deps={p.key:set()},standing={p.key:"ALIVE"},candidates=[Candidate("lease-gate",9,10,True)])
  self.assertEqual(plan["phases"],["VERIFY","CONSTRUCT"]); self.assertTrue(replay(r))
  self.assertFalse(replay(Receipt(r.schema,{**r.payload,"actuation_performed":True},r.digest)))
