import unittest
from datetime import datetime, timezone
from scripts.release_train.invalidation_promotion.subject import Subject
from scripts.release_train.invalidation_promotion.binding import PromotionBinding
from scripts.release_train.invalidation_promotion.event import InvalidationEvent
from scripts.release_train.invalidation_promotion.cascade import build_cascade
class T(unittest.TestCase):
 def test_reason_and_depth(self):
  a=Subject('x/a','a'*40); b=Subject('x/b','b'*40); c=Subject('x/c','c'*40); r='d'*64
  bs=[PromotionBinding(b,a,r,'v1','REPOSITORY','1'),PromotionBinding(c,b,r,'v1','REPOSITORY','2')]
  out=build_cascade(bs,InvalidationEvent(a,'BUILD_BROKEN',datetime.now(timezone.utc)))
  self.assertEqual([(x.depth,x.reason) for x in out],[(1,'PRODUCER_BUILD_BROKEN'),(2,'PRODUCER_BUILD_BROKEN')])
