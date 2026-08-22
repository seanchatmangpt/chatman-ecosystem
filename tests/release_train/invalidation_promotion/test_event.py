import unittest
from datetime import datetime, timezone
from scripts.release_train.invalidation_promotion.subject import Subject, Refusal
from scripts.release_train.invalidation_promotion.event import InvalidationEvent
class T(unittest.TestCase):
 def test_event_contract(self):
  s=Subject('a/b','a'*40); now=datetime.now(timezone.utc)
  self.assertEqual(InvalidationEvent(s,'BUILD_BROKEN',now).kind,'BUILD_BROKEN')
  with self.assertRaises(Refusal): InvalidationEvent(s,'NEW_RECEIPT',now)
