import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.promotion_recovery.lease import IntentLease
class T(unittest.TestCase):
 def test_half_open(self):
  a=datetime(2026,1,1,tzinfo=timezone.utc); l=IntentLease(a,a+timedelta(hours=1))
  self.assertTrue(l.active(a)); self.assertFalse(l.active(a+timedelta(hours=1)))
