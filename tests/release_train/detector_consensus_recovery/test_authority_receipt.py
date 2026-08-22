import unittest
from scripts.release_train.detector_consensus_recovery.authority import admit_action,qualification_plan
from scripts.release_train.detector_consensus_recovery.receipt import issue,replay,Receipt
class Court(unittest.TestCase):
 def test_do_refused(self):
  with self.assertRaisesRegex(PermissionError,"BRCE_REQUIRED"): admit_action("DO")
  self.assertEqual(qualification_plan(),("VERIFY","CONSTRUCT"))
 def test_receipt_replay_and_tamper(self):
  r=issue({"x":1}); self.assertTrue(replay(r)); bad=Receipt({**r.payload,"x":2},r.digest)
  with self.assertRaisesRegex(ValueError,"RECEIPT_TAMPER"): replay(bad)
