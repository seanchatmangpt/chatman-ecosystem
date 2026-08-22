from datetime import datetime,timedelta,timezone
import unittest
from scripts.develop_train.selection_intent_runtime.identity import Subject
from scripts.develop_train.selection_intent_runtime.frontier import CutCandidate,CandidateFrontier
from scripts.develop_train.selection_intent_runtime.intent import IntentLease,SelectionIntent
from scripts.develop_train.selection_intent_runtime.policy import StrategyPolicy,CutStrategy
from scripts.develop_train.selection_intent_runtime.proof import SelectionProof
class TestProof(unittest.TestCase):
 def test_current_and_stale_policy(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject("a/x@"+"a"*40); f=CandidateFrontier((CutCandidate("old",5,((s,9),),t),CutCandidate("new",6,((s,8),),t))); p=StrategyPolicy(CutStrategy.LATEST_COMPLETE); i=SelectionIntent(s,"new",p.digest,f.digest,"n",IntentLease(t,t+timedelta(hours=1)))
  self.assertEqual(SelectionProof(i).admit(f,p).cut_id,"new")
  with self.assertRaisesRegex(ValueError,"STALE_SELECTION_POLICY"): SelectionProof(i).admit(f,StrategyPolicy(CutStrategy.MAX_FRESHNESS))
