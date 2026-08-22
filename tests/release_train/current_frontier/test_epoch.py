import unittest
from datetime import datetime, timezone
from scripts.release_train.current_frontier.epoch import Epoch, Refusal
class T(unittest.TestCase):
 def test_half_open(self):
  e=Epoch(datetime(2026,1,1,tzinfo=timezone.utc),datetime(2026,1,2,tzinfo=timezone.utc)); self.assertTrue(e.contains(e.start)); self.assertFalse(e.contains(e.end))
 def test_naive_refuses(self):
  with self.assertRaises(Refusal): Epoch(datetime(2026,1,1),datetime(2026,1,2))
