import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.recovery_witness.lease import WitnessLease
class T(unittest.TestCase):
 def test_half_open(self):
  now=datetime.now(timezone.utc); lease=WitnessLease(now,now+timedelta(seconds=1))
  self.assertTrue(lease.active(now)); self.assertFalse(lease.active(lease.expires_at))
