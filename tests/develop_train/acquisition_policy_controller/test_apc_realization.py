from datetime import datetime, timezone, timedelta
from scripts.develop_train.acquisition_policy_controller.subject import Subject, Refusal
from scripts.develop_train.acquisition_policy_controller.realization import Realization
S=Subject("seanchatmangpt/chatman-ecosystem","a"*40)
NOW=datetime.now(timezone.utc)-timedelta(seconds=1)
import unittest
class T(unittest.TestCase):
    def test_naive_future_and_strategy_refused(self):
        with self.assertRaises(Refusal): Realization(S,"p","c","BAD",1,.1,.1,1,1,1,1,NOW,"PASS")
        with self.assertRaises(Refusal): Realization(S,"p","c","MAX_INFORMATION_GAIN",1,.1,.1,1,1,1,1,datetime.now(),"PASS")
