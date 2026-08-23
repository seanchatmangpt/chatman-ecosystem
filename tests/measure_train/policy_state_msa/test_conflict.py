import unittest
from datetime import datetime,timezone
from scripts.measure_train.policy_state_msa.subject import Subject
from scripts.measure_train.policy_state_msa.state import PolicyState
from scripts.measure_train.policy_state_msa.transition import Transition
from scripts.measure_train.policy_state_msa.conflict import classify_conflicts
class T(unittest.TestCase):
    def test_aba_recurrence(self):
        s=Subject("o/r","a"*40); a=PolicyState(s,1,1,"1"*64,"a"*64); b=PolicyState(s,1,2,"2"*64,"b"*64); c=PolicyState(s,1,3,"3"*64,"a"*64); n=datetime.now(timezone.utc)
        rows=[Transition(a,b,1,a.digest,"COMMITTED",n,n,"w1","e1"),Transition(b,c,2,b.digest,"COMMITTED",n,n,"w2","e2")]
        self.assertIn(("e2","ABA_VALUE_RECURRENCE"),classify_conflicts(rows))
