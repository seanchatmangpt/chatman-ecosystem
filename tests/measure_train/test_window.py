import unittest
from datetime import datetime, timezone
from scripts.measure_train.window import Window
from scripts.measure_train.identity import Refused
class WindowCourt(unittest.TestCase):
    def setUp(self): self.w=Window(datetime(2026,8,22,4,tzinfo=timezone.utc),datetime(2026,8,22,6,tzinfo=timezone.utc))
    def test_half_open(self):
        self.assertTrue(self.w.contains("2026-08-22T04:00:00Z")); self.assertFalse(self.w.contains("2026-08-22T06:00:00Z"))
    def test_reverse_refuses(self):
        with self.assertRaises(Refused): Window(self.w.until,self.w.since)
    def test_naive_refuses(self):
        with self.assertRaises(Refused): self.w.contains("2026-08-22T05:00:00")
if __name__=='__main__': unittest.main()
