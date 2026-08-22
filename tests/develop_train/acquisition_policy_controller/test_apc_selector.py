from datetime import datetime, timezone, timedelta
from scripts.develop_train.acquisition_policy_controller.subject import Subject
from scripts.develop_train.acquisition_policy_controller.realization import Realization
from scripts.develop_train.acquisition_policy_controller.evidence import aggregate
from scripts.develop_train.acquisition_policy_controller.policy import Policy
from scripts.develop_train.acquisition_policy_controller.selector import score,select
S=Subject("seanchatmangpt/chatman-ecosystem","a"*40); NOW=datetime.now(timezone.utc)-timedelta(seconds=1)
def row(strategy,gain,cid): return Realization(S,"p",cid,strategy,1,.2,gain,1,1,10,10,NOW,"PASS")
import unittest
class T(unittest.TestCase):
    def test_best_admissible_strategy(self):
        rows=[row("MAX_INFORMATION_GAIN",.8,"a"),row("MAX_INFORMATION_PER_COST",.2,"b"),row("MIN_EXPECTED_ENTROPY",.1,"c")]
        ev=aggregate(rows); pol=Policy(1,0,1,10,100,.5); scores=[score(e,3,pol) for e in ev.values()]
        self.assertEqual(select(scores).strategy,"MAX_INFORMATION_GAIN")
