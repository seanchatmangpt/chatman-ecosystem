import unittest
from scripts.release_train.recovery_evidence_quorum.subject import Subject
class T(unittest.TestCase):
 def test_exact(self): self.assertTrue(Subject("o/r","a"*40).key.endswith("a"*40))
 def test_short(self):
  with self.assertRaisesRegex(ValueError,"INEXACT_SUBJECT"): Subject("o/r","abc")
