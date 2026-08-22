import unittest
from datetime import datetime, timezone
from scripts.release_train.invalidation_promotion.subject import Subject
from scripts.release_train.invalidation_promotion.binding import PromotionBinding
from scripts.release_train.invalidation_promotion.event import InvalidationEvent
from scripts.release_train.invalidation_promotion.engine import qualify_invalidation
from scripts.release_train.invalidation_promotion.receipt import replay_receipt
class T(unittest.TestCase):
 def test_transitive_revocation_and_replay(self):
  p=Subject('x/p','a'*40); c=Subject('x/c','b'*40); d=Subject('x/d','c'*40); r='d'*64
  bs=[PromotionBinding(c,p,r,'v1','REPOSITORY','pc'),PromotionBinding(d,c,r,'v1','REPOSITORY','cd')]
  out=qualify_invalidation(bs,InvalidationEvent(p,'BUILD_BROKEN',datetime.now(timezone.utc)),{c.key:'PARTIAL_ALIVE',d.key:'PARTIAL_ALIVE'},transactional=True)
  self.assertEqual(out['payload']['standings'],{c.key:'BLOCKED',d.key:'BLOCKED'})
  self.assertEqual(out['payload']['candidate'],'sqlite')
  self.assertFalse(out['actuation_performed'])
  self.assertTrue(replay_receipt(out['receipt']))
  self.assertTrue(all(x['phase'] in {'VERIFY','CONSTRUCT'} for x in out['payload']['plan']))
