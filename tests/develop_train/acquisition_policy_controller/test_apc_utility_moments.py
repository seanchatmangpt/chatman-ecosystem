from datetime import datetime, timezone, timedelta
from scripts.develop_train.acquisition_policy_controller.subject import Subject
from scripts.develop_train.acquisition_policy_controller.realization import Realization
from scripts.develop_train.acquisition_policy_controller.utility import utility
from scripts.develop_train.acquisition_policy_controller.moments import Moments
S=Subject("seanchatmangpt/chatman-ecosystem","a"*40)
NOW=datetime.now(timezone.utc)-timedelta(seconds=1)
def row(outcome="PASS"):
    return Realization(S,"p","c","MAX_INFORMATION_GAIN",1,.35,.4,1,1,10,10,NOW,outcome)
import unittest
class T(unittest.TestCase):
    def test_risk_and_online_moments(self):
        self.assertGreater(utility(row("PASS")).score,utility(row("FAIL")).score)
        m=Moments().update(1).update(3)
        self.assertEqual(m.mean,2); self.assertGreater(m.variance,0)
