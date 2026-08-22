import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.promotion_recovery.subject import Subject
from scripts.release_train.promotion_recovery.policy import StrategyPolicy
from scripts.release_train.promotion_recovery.frontier import *
from scripts.release_train.promotion_recovery.lease import IntentLease
from scripts.release_train.promotion_recovery.intent import PromotionIntent
from scripts.release_train.promotion_recovery.proof import SelectionProof
from scripts.release_train.promotion_recovery.compatibility import *
from scripts.release_train.promotion_recovery.recovery import RecoveryStrategy
from scripts.release_train.promotion_recovery.dependency import DependencyGraph
from scripts.release_train.promotion_recovery.engine import deterministic_json
class T(unittest.TestCase):
 def test_policy_drift_requalifies_deterministically_without_do(self):
  now=datetime(2026,8,22,16,tzinfo=timezone.utc)
  oldf=CandidateFrontier([CutCandidate('a',1,2,0),CutCandidate('b',2,1,0)])
  oldp=StrategyPolicy('LATEST_COMPLETE')
  intent=PromotionIntent(Subject('seanchatmangpt/chatman-ecosystem','f'*40),'b',oldp.digest,oldf.digest,'n',IntentLease(now-timedelta(minutes=5),now+timedelta(hours=1)))
  proof=SelectionProof('b',oldp.digest,oldf.digest)
  newp=StrategyPolicy('MAX_FRESHNESS')
  witness=CompatibilityWitness(CompatibilityKind.BACKWARD_COMPATIBLE,oldp.digest,newp.digest,'measure-107')
  g=DependencyGraph({'consumer':['producer'],'producer':[]})
  kw=dict(intent=intent,proof=proof,policy=newp,frontier=oldf,now=now,witness=witness,recovery_strategy=RecoveryStrategy.REQUALIFY_COMPATIBLE,dependency_graph=g,dependency_standings={'producer':'PARTIAL_ALIVE'})
  a=deterministic_json(**kw); b=deterministic_json(**kw)
  self.assertEqual(a,b); self.assertIn('REQUALIFYING',a); self.assertIn('"actuation_performed":false',a); self.assertIn('VERIFY',a); self.assertIn('CONSTRUCT',a)
