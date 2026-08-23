import unittest
from datetime import datetime,timezone
from scripts.measure_train.policy_state_msa.subject import Subject
from scripts.measure_train.policy_state_msa.state import PolicyState
from scripts.measure_train.policy_state_msa.transition import Transition
from scripts.measure_train.policy_state_msa.linearization import cas_linearization
class T(unittest.TestCase):
    def test_single_commit_linearizes(self):
        s=Subject("o/r","a"*40); a=PolicyState(s,1,1,"1"*64,"a"*64); b=PolicyState(s,1,2,"2"*64,"b"*64); n=datetime.now(timezone.utc); t=Transition(a,b,1,a.digest,"COMMITTED",n,n,"w","e")
        self.assertEqual(cas_linearization([t]),("e",))
