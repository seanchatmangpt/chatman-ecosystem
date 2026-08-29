import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.promotion_epoch.epoch import Epoch,EpochRefusal
class T(unittest.TestCase):
 def test_half_open(self):
  s=datetime(2026,1,1,tzinfo=timezone.utc); e=Epoch(s,s+timedelta(hours=2))
  self.assertTrue(e.contains(s)); self.assertFalse(e.contains(s+timedelta(hours=2)))
 def test_naive_refuses(self):
  with self.assertRaises(EpochRefusal): Epoch(datetime(2026,1,1),datetime(2026,1,2))
