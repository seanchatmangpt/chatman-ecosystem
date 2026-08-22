import unittest
from datetime import datetime,timezone
from scripts.develop_train.ack_discharge.engine import qualify
from scripts.develop_train.ack_discharge.event import *
from scripts.develop_train.ack_discharge.frontier import AckFrontier
from scripts.develop_train.ack_discharge.persistence import StoreRequirements
from scripts.develop_train.ack_discharge.receipt import replay
from scripts.develop_train.ack_discharge.strategy import Strategy
from scripts.develop_train.ack_discharge.subject import Subject
from scripts.develop_train.ack_discharge.topology import ConsumerNode,DependencyTopology
class T(unittest.TestCase):
 def test_e2e(self):
  p=Subject('o/p','a'*40);a=ConsumerNode(Subject('o/a','b'*40),True);b=ConsumerNode(Subject('o/b','c'*40));g=DependencyTopology(p,[a,b],[(p.identity,a.subject.identity),(p.identity,b.subject.identity)]);e=InvalidationEvent(p,InvalidationKind.BUILD_BROKEN,'ev',datetime.now(timezone.utc));f=AckFrontier.from_consumers([(a.subject,True),(b.subject,False)]);f.record(a.subject,'ra')
  q=qualify(producer=p,event=e,topology=g,frontier=f,strategy=Strategy.CRITICAL_PATH,requirements=StoreRequirements(durable=True),evidence={'a':'ra'})
  self.assertTrue(q.complete);self.assertEqual(q.standing,'PARTIAL_ALIVE');self.assertEqual(q.store,'JSONL');self.assertTrue(replay(q.receipt,q.receipt_digest));self.assertFalse(q.receipt.actuation_performed)
