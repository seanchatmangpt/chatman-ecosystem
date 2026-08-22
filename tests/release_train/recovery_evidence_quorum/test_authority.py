import unittest
from scripts.release_train.recovery_evidence_quorum.authority import require_action
class T(unittest.TestCase):
 def test_construct(self): self.assertEqual(require_action("CONSTRUCT"),"CONSTRUCT")
 def test_do(self):
  with self.assertRaisesRegex(PermissionError,"BRCE_REQUIRED"): require_action("DO")
