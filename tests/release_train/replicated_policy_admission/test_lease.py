import unittest
from fixtures import lease,NOW
class TestLease(unittest.TestCase):
    def test_half_open(self):
        l=lease(); self.assertTrue(l.admits(l.not_before)); self.assertFalse(l.admits(l.expires_at)); self.assertTrue(l.admits(NOW))
