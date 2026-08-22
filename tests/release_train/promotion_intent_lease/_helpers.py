from datetime import datetime, timezone, timedelta
from scripts.release_train.promotion_intent_lease.subject import Subject
from scripts.release_train.promotion_intent_lease.cut import CutIdentity
from scripts.release_train.promotion_intent_lease.strategy import StrategyBinding
from scripts.release_train.promotion_intent_lease.intent import PromotionIntent
from scripts.release_train.promotion_intent_lease.lease import IntentLease
from scripts.release_train.promotion_intent_lease.frontier import PromotionFrontier

S1=Subject.parse('seanchatmangpt/chatman-ecosystem@'+'1'*40)
S2=Subject.parse('seanchatmangpt/gymact@'+'2'*40)
NOW=datetime(2026,8,22,15,0,tzinfo=timezone.utc)
CUT=CutIdentity('cut-7',7,(S2,))
STRAT=StrategyBinding.from_name('MIN_SKEW',(('tie','freshness'),))
POL='a'*64
INTENT=PromotionIntent(S1,CUT,STRAT,POL,'nonce-1')
LEASE=IntentLease(NOW-timedelta(minutes=5),NOW+timedelta(minutes=5))
FRONTIER=PromotionFrontier(CUT,STRAT,POL)
