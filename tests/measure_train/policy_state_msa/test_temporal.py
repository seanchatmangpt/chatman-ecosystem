import unittest
from datetime import datetime,timezone
from scripts.measure_train.policy_state_msa.subject import Subject
from scripts.measure_train.policy_state_msa.state import PolicyState
from scripts.measure_train.policy_state_msa.transition import Transition
from scripts.measure_train.policy_state_msa.temporal import monitor_trace
class T(unittest.TestCase):
    def test_clean_trace(self):
        s=Subject("o/r","a"*40); a=PolicyState(s,1,1,"1"*64,"a"*64); b=PolicyState(s,1,2,"2"*64,"b"*64); n=datetime.now(timezone.utc)
        self.assertEqual(monitor_trace([Transition(a,b,1,a.digest,"COMMITTED",n,n,"w","e")]),())
