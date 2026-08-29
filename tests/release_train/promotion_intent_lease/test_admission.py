import unittest
from scripts.release_train.promotion_intent_lease.admission import admit_intent
from scripts.release_train.promotion_intent_lease.frontier import PromotionFrontier
from scripts.release_train.promotion_intent_lease.strategy import StrategyBinding
from scripts.release_train.promotion_intent_lease.subject import Refusal
from _helpers import INTENT,LEASE,FRONTIER,NOW,CUT,POL
class T(unittest.TestCase):
 def test_current_and_strategy_drift(self):
  admit_intent(INTENT,LEASE,FRONTIER,NOW)
  bad=PromotionFrontier(CUT,StrategyBinding.from_name('LATEST_COMPLETE'),POL)
  with self.assertRaisesRegex(Refusal,'STALE_SELECTION_STRATEGY'): admit_intent(INTENT,LEASE,bad,NOW)
