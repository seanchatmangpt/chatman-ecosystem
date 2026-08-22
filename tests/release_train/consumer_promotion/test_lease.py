import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.consumer_promotion.lease import EvidenceLease
class T(unittest.TestCase):
 def test_half_open(self):
  a=datetime(2026,1,1,tzinfo=timezone.utc); l=EvidenceLease(a,a+timedelta(hours=1))
  self.assertTrue(l.active(a)); self.assertFalse(l.active(a+timedelta(hours=1)))
