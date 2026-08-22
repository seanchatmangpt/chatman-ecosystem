import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.cut_epoch.lease import CutLease
from scripts.measure_train.cut_epoch.subject import Refused
class T(unittest.TestCase):
 def test_interval(self):
  now=datetime.now(timezone.utc); self.assertGreater(CutLease("a"*64,now,now+timedelta(seconds=1)).expires_at,now)
  with self.assertRaises(Refused): CutLease("a"*64,now,now)
