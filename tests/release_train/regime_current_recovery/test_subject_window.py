import unittest
from datetime import timedelta
from scripts.release_train.regime_current_recovery.subject import Subject,Refusal
from scripts.release_train.regime_current_recovery.window import CalibrationWindow
from fixtures import NOW
class T(unittest.TestCase):
 def test_exact(self):
  s=Subject('a/b','a'*40); self.assertEqual(s.exact,'a/b@'+'a'*40); w=CalibrationWindow(NOW-timedelta(hours=1),NOW); self.assertTrue(w.contains(NOW-timedelta(seconds=1))); self.assertFalse(w.contains(NOW))
 def test_refuse(self):
  with self.assertRaisesRegex(Refusal,'INEXACT_SUBJECT'): Subject('a/b','main')
  with self.assertRaisesRegex(Refusal,'NAIVE_TIME'): CalibrationWindow(NOW.replace(tzinfo=None),NOW)
