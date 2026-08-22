import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.delta.freshness import classify_freshness
class T(unittest.TestCase):
 def test_stale_future_and_unbounded(self):
  now=datetime.now(timezone.utc); self.assertEqual(classify_freshness(now-timedelta(seconds=61),now,60),"STALE"); self.assertEqual(classify_freshness(now+timedelta(seconds=1),now,60),"REFUSED[FUTURE_EVIDENCE]"); self.assertEqual(classify_freshness(now,now,None),"UNBOUNDED")
