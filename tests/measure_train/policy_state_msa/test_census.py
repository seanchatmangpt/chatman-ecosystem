import unittest
from datetime import datetime,timezone
from scripts.measure_train.policy_state_msa.subject import Subject
from scripts.measure_train.policy_state_msa.state import PolicyState
from scripts.measure_train.policy_state_msa.transition import Transition
from scripts.measure_train.policy_state_msa.calibration import Calibration
from scripts.measure_train.policy_state_msa.census import census
class T(unittest.TestCase):
    def test_failure_dominates(self):
        s=Subject("o/r","a"*40); a=PolicyState(s,1,1,"1"*64,"a"*64); b=PolicyState(s,1,2,"2"*64,"b"*64); n=datetime.now(timezone.utc); t=Transition(a,b,1,a.digest,"COMMITTED",n,n,"w","e"); cal=Calibration(10,10,0,0,0,1,0,.72,"CALIBRATED")
        self.assertEqual(census([t],(),(("e","violation"),),"PASS",cal)["standing"],"BUILD_BROKEN")
