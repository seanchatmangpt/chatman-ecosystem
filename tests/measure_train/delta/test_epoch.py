import unittest
from datetime import datetime,timezone
from scripts.measure_train.delta.epoch import Epoch
class T(unittest.TestCase):
 def test_timezone_boundary(self):
  e=Epoch(datetime(2026,1,1,tzinfo=timezone.utc)); self.assertEqual(e.age_seconds(datetime(2026,1,1,0,1,tzinfo=timezone.utc)),60)
  with self.assertRaises(ValueError): Epoch(datetime(2026,1,1))
