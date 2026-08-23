import unittest
from datetime import datetime,timezone
from scripts.measure_train.policy_state_msa.subject import Subject
from scripts.measure_train.policy_state_msa.state import PolicyState
from scripts.measure_train.policy_state_msa.transition import Transition
from scripts.measure_train.policy_state_msa.durability import RestartWitness
from scripts.measure_train.policy_state_msa.fault_trial import FaultTrial
from scripts.measure_train.policy_state_msa.qualify import qualify
from scripts.measure_train.policy_state_msa.replay import replay
class T(unittest.TestCase):
    def test_chicago_policy_state_msa(self):
        s=Subject("o/r","a"*40); a=PolicyState(s,1,1,"1"*64,"a"*64); b=PolicyState(s,1,2,"2"*64,"b"*64); n=datetime.now(timezone.utc); t=Transition(a,b,1,a.digest,"COMMITTED",n,n,"w","e")
        trials=[FaultTrial("STALE_CAS",True,True,f"s{i}") for i in range(12)]+[FaultTrial("RESTART",False,False,f"g{i}") for i in range(4)]
        q=qualify(s,[t],RestartWitness(s.sha,2,2,b.digest,b.digest,False,True),trials)
        self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
