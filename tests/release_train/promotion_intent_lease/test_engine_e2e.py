import unittest
from scripts.release_train.promotion_intent_lease.engine import qualify
from scripts.release_train.promotion_intent_lease.dependency import DependencyGraph
from scripts.release_train.promotion_intent_lease.candidate import PersistenceNeed
from _helpers import *
class T(unittest.TestCase):
 def test_dependency_closed_non_actuating_qualification(self):
  q=qualify(INTENT,LEASE,FRONTIER,NOW,DependencyGraph(((S1,S2),)),('PASS','PASS'),PersistenceNeed(transactional=True))
  self.assertEqual(q.standing,'PARTIAL_ALIVE'); self.assertEqual(q.store,'SQLITE')
  self.assertEqual(q.plan.phases,('VERIFY','CONSTRUCT')); self.assertTrue(q.receipt.replay()); self.assertFalse(q.receipt.payload['actuation_performed'])
