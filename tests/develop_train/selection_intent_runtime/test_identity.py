from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.selection_intent_runtime.identity import Subject
class TestIdentity(unittest.TestCase):
 def test_exact_subject_and_short_refusal(self):
  s=Subject("acme/a@"+"a"*40); self.assertEqual(s.sha,"a"*40)
  with self.assertRaisesRegex(ValueError,"INEXACT_SUBJECT"): Subject("acme/a@main")
