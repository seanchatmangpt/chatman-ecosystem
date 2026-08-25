from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.develop_train.process_convergence_substrate import *
import unittest

BASE=datetime(2026,8,23,9,0,tzinfo=timezone.utc)
def subj(gen,ch): return SubjectEpoch(f"seanchatmangpt/chatman-ecosystem@{ch*40}",gen)
def epoch(gen,ch,states,minute=0):
    return ClosureEpoch(subj(gen,ch),BASE+timedelta(minutes=minute),tuple(Obligation(k,State[v],Fraction(w,1)) for k,v,w in states))

class TestChicago(unittest.TestCase):
    def test_transition_series_cannot_launder_live_failure(self):
        a=epoch(10,"a",[("semantic","PASS",3),("powl","PASS",2),("reactor","FAIL",4),("tls","FAIL",5)],0)
        b=epoch(11,"b",[("semantic","PASS",3),("powl","PASS",2),("reactor","PASS",4),("tls","FAIL",5)],1)
        c=epoch(12,"c",[("semantic","PASS",3),("powl","PASS",2),("reactor","PASS",4),("tls","FAIL",5)],2)
        t=Trajectory((a,b,c))
        g=DependencyGraph({"tls":("reactor",),"reactor":("semantic",)})
        q=qualify(t,g)
        self.assertEqual(q.standing,"BUILD_BROKEN")
        self.assertTrue(replay(q.receipt,q.receipt.digest()))
        self.assertFalse(q.receipt.actuation_performed)
    def test_clean_monotone_path_caps_at_partial_alive(self):
        a=epoch(20,"d",[("semantic","UNKNOWN",1),("reactor","UNKNOWN",1)],0)
        b=epoch(21,"e",[("semantic","PASS",1),("reactor","UNKNOWN",1)],1)
        c=epoch(22,"f",[("semantic","PASS",1),("reactor","PASS",1)],2)
        q=qualify(Trajectory((a,b,c)),DependencyGraph({"reactor":("semantic",)}))
        self.assertEqual(q.direction,"CONVERGING")
        self.assertEqual(q.standing,"PARTIAL_ALIVE")
