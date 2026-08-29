import unittest
from datetime import timedelta
from scripts.release_train.detector_consensus_recovery.subject import Subject
from scripts.release_train.detector_consensus_recovery.window import EvaluationWindow
from helpers import S,NOW
class Court(unittest.TestCase):
 def test_exact_subject(self):
  self.assertEqual(S.identity,"seanchatmangpt/chatman-ecosystem@"+"0"*40)
  with self.assertRaisesRegex(ValueError,"INEXACT_SUBJECT"): Subject("bad","abc")
 def test_half_open(self):
  w=EvaluationWindow(NOW,NOW+timedelta(hours=1)); self.assertTrue(w.contains(NOW)); self.assertFalse(w.contains(w.end))
