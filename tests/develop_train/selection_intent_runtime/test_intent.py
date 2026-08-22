from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.selection_intent_runtime.identity import Subject
from scripts.develop_train.selection_intent_runtime.intent import *
class TestIntent(unittest.TestCase):
 def test_half_open_lease(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); l=IntentLease(t,t+timedelta(hours=1)); self.assertTrue(l.active(t)); self.assertFalse(l.active(t+timedelta(hours=1)))
  with self.assertRaisesRegex(ValueError,"INVALID_INTENT_LEASE"): IntentLease(t,t)
  SelectionIntent(Subject("a/x@"+"a"*40),"c","a"*64,"b"*64,"n",l)
