from datetime import datetime,timedelta,timezone
import unittest
from scripts.develop_train.selection_intent_runtime.identity import Subject
from scripts.develop_train.selection_intent_runtime.frontier import CutCandidate,CandidateFrontier
from scripts.develop_train.selection_intent_runtime.intent import IntentLease,SelectionIntent
from scripts.develop_train.selection_intent_runtime.policy import StrategyPolicy,CutStrategy
from scripts.develop_train.selection_intent_runtime.engine import qualify
from scripts.develop_train.selection_intent_runtime.recovery import RecoveryStrategy
from scripts.develop_train.selection_intent_runtime.receipt import replay
class TestE2E(unittest.TestCase):
 def test_policy_movement_reselects_and_never_actuates(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject("a/x@"+"a"*40); f=CandidateFrontier((CutCandidate("old",5,((s,9),),t),CutCandidate("new",6,((s,8),),t))); p=StrategyPolicy(CutStrategy.LATEST_COMPLETE); i=SelectionIntent(s,"new",p.digest,f.digest,"n",IntentLease(t,t+timedelta(hours=1)))
  q=qualify(intent=i,frontier=f,policy=p,recovery=RecoveryStrategy.RESELECT,now=t); self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertTrue(replay(q.receipt,q.receipt.digest))
  moved=StrategyPolicy(CutStrategy.MAX_FRESHNESS); q2=qualify(intent=i,frontier=f,policy=moved,recovery=RecoveryStrategy.RESELECT,now=t); self.assertEqual(q2.standing,"REQUALIFYING"); self.assertEqual(q2.selected_cut_id,"old"); self.assertFalse(q2.receipt.actuation_performed)
