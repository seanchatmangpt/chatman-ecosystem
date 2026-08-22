from datetime import datetime, timezone, timedelta
from scripts.develop_train.acquisition_policy_controller.subject import Subject, Refusal
from scripts.develop_train.acquisition_policy_controller.realization import Realization
S=Subject("seanchatmangpt/chatman-ecosystem","a"*40)
NOW=datetime.now(timezone.utc)-timedelta(seconds=1)
def row(strategy="MAX_INFORMATION_GAIN",gain=.4,pred=.35,cost=1.0,lat=10.0,outcome="PASS",gen=1,cid="c"):
    return Realization(S,"p",cid,strategy,gen,pred,gain,1.0,cost,10.0,lat,NOW,outcome)
import unittest
class T(unittest.TestCase):
    def test_exact(self): self.assertTrue(S.exact.endswith("@"+"a"*40))
    def test_short_refused(self):
        with self.assertRaises(Refusal): Subject("seanchatmangpt/chatman-ecosystem","abc")
