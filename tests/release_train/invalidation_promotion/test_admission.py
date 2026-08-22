import unittest
from datetime import datetime, timezone
from scripts.release_train.invalidation_promotion.subject import Subject, Refusal
from scripts.release_train.invalidation_promotion.binding import PromotionBinding
from scripts.release_train.invalidation_promotion.event import InvalidationEvent
from scripts.release_train.invalidation_promotion.admission import admit_event
class T(unittest.TestCase):
 def test_orphan_refusal(self):
  a=Subject('x/a','a'*40); b=Subject('x/b','b'*40); bd=PromotionBinding(b,a,'c'*64,'v1','REPOSITORY','id')
  self.assertEqual(len(admit_event([bd],InvalidationEvent(a,'NEW_HEAD',datetime.now(timezone.utc)))),1)
  with self.assertRaises(Refusal): admit_event([bd],InvalidationEvent(b,'NEW_HEAD',datetime.now(timezone.utc)))
