import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consumer_binding.lease import EvidenceLease
from scripts.measure_train.consumer_binding.subject import Refused
class T(unittest.TestCase):
 def test_interval(self):
  now=datetime.now(timezone.utc)
  self.assertGreater(EvidenceLease("a"*64,now,now+timedelta(seconds=1)).expires_at,now)
  with self.assertRaises(Refused): EvidenceLease("a"*64,now,now)
