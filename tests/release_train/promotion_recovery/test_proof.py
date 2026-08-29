import unittest
from scripts.release_train.promotion_recovery.frontier import *
from scripts.release_train.promotion_recovery.policy import StrategyPolicy
from scripts.release_train.promotion_recovery.proof import SelectionProof
from scripts.release_train.promotion_recovery.subject import Refusal
class T(unittest.TestCase):
 def test_stale_frontier_refuses(self):
  p=StrategyPolicy('LATEST_COMPLETE'); f=CandidateFrontier([CutCandidate('a',1,1,0)])
  proof=SelectionProof('a',p.digest,'0'*64)
  with self.assertRaisesRegex(Refusal,'STALE_CANDIDATE_FRONTIER'): proof.admit(p,f)
