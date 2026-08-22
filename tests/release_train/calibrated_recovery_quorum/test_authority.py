import unittest
from scripts.release_train.calibrated_recovery_quorum.authority import require_action
class T(unittest.TestCase):
 def test_do_refuses(self):
  self.assertEqual(require_action("CONSTRUCT").value,"CONSTRUCT")
  with self.assertRaises(Exception): require_action("DO")
