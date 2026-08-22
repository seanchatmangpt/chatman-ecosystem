import unittest
from _helpers import LEASE
class T(unittest.TestCase):
 def test_half_open(self):
  self.assertTrue(LEASE.active(LEASE.not_before)); self.assertFalse(LEASE.active(LEASE.expires_at))
