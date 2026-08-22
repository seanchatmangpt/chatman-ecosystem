from datetime import datetime,timedelta,timezone
import unittest
from scripts.develop_train.selection_intent_runtime.identity import Subject
from scripts.develop_train.selection_intent_runtime.frontier import CutCandidate,CandidateFrontier
from scripts.develop_train.selection_intent_runtime.intent import IntentLease,SelectionIntent
from scripts.develop_train.selection_intent_runtime.policy import StrategyPolicy,CutStrategy
from scripts.develop_train.selection_intent_runtime.drift import classify,DriftKind
class TestDrift(unittest.TestCase):
 def test_policy_and_expiry_distinct(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject("a/x@"+"a"*40); f=CandidateFrontier((CutCandidate("new",6,((s,8),),t),)); p=StrategyPolicy(CutStrategy.LATEST_COMPLETE); i=SelectionIntent(s,"new",p.digest,f.digest,"n",IntentLease(t,t+timedelta(hours=1)))
  self.assertEqual(classify(i,p,f,t).kind,DriftKind.EXACT); self.assertEqual(classify(i,StrategyPolicy(CutStrategy.MAX_FRESHNESS),f,t).kind,DriftKind.POLICY); self.assertEqual(classify(i,p,f,t+timedelta(hours=1)).kind,DriftKind.LEASE_EXPIRED)
