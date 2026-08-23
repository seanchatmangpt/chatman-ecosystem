import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.replicated_evidence_state.lease import Lease

class LeaseTest(unittest.TestCase):
    def test_half_open_boundary(self):
        start=datetime(2026,8,22,tzinfo=timezone.utc); end=start+timedelta(seconds=10); lease=Lease(start,end)
        self.assertTrue(lease.admits(start)); self.assertFalse(lease.admits(end))
