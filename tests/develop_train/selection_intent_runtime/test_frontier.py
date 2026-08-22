from datetime import datetime, timedelta, timezone
import unittest
from scripts.develop_train.selection_intent_runtime.identity import Subject
from scripts.develop_train.selection_intent_runtime.frontier import *
class TestFrontier(unittest.TestCase):
 def test_digest_order_and_duplicate_refusal(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject("a/x@"+"a"*40); a=CutCandidate("a",1,((s,1),),t); b=CutCandidate("b",2,((s,2),),t)
  self.assertEqual(CandidateFrontier((a,b)).digest,CandidateFrontier((b,a)).digest)
  with self.assertRaisesRegex(ValueError,"INVALID_CANDIDATE_FRONTIER"): CandidateFrontier((a,a))
