import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.promotion_recovery.subject import Subject
from scripts.release_train.promotion_recovery.policy import StrategyPolicy
from scripts.release_train.promotion_recovery.frontier import *
from scripts.release_train.promotion_recovery.lease import IntentLease
from scripts.release_train.promotion_recovery.intent import PromotionIntent
from scripts.release_train.promotion_recovery.drift import classify,DriftKind
class T(unittest.TestCase):
 def test_policy_movement_is_typed(self):
  now=datetime(2026,1,1,tzinfo=timezone.utc); f=CandidateFrontier([CutCandidate('a',1,1,0)]); p=StrategyPolicy('LATEST_COMPLETE')
  i=PromotionIntent(Subject('o/r','a'*40),'a',p.digest,f.digest,'n',IntentLease(now,now+timedelta(hours=1)))
  self.assertEqual(classify(i,StrategyPolicy('MAX_FRESHNESS'),f,now),DriftKind.POLICY)
