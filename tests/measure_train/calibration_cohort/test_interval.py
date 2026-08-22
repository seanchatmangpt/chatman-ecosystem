import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.calibration_cohort.interval import Interval,intersection,overlap_ratio
class T(unittest.TestCase):
 def test_half_open_overlap(self):
  n=datetime.now(timezone.utc); a=Interval(n,n+timedelta(seconds=10)); b=Interval(n+timedelta(seconds=5),n+timedelta(seconds=15))
  self.assertEqual(intersection([a,b]).micros(),5_000_000); self.assertEqual(overlap_ratio([a,b]),Fraction(1,3))
