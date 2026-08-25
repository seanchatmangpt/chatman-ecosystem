from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.develop_train.process_convergence_substrate import *
from scripts.develop_train.process_convergence_substrate.policy import Strategy,classify
import unittest

BASE=datetime(2026,8,23,9,0,tzinfo=timezone.utc)
def subj(gen,ch): return SubjectEpoch(f"seanchatmangpt/chatman-ecosystem@{ch*40}",gen)
def epoch(gen,ch,states,minute=0):
    return ClosureEpoch(subj(gen,ch),BASE+timedelta(minutes=minute),tuple(Obligation(k,State[v],Fraction(w,1)) for k,v,w in states))

class TestDependencyPolicy(unittest.TestCase):
    def test_blocking_cut_and_strategy_noncollapse(self):
        a=epoch(1,"a",[("semantic","PASS",1),("reactor","FAIL",2),("global","UNKNOWN",1)],0)
        b=epoch(2,"b",[("semantic","PASS",1),("reactor","BLOCKED",2),("global","UNKNOWN",1)],1)
        c=epoch(3,"c",[("semantic","PASS",1),("reactor","UNKNOWN",2),("global","UNKNOWN",1)],2)
        t=Trajectory((a,b,c))
        g=DependencyGraph({"global":("reactor",),"reactor":("semantic",)})
        self.assertEqual(g.blocking_cut(b),frozenset({"reactor"}))
        out={s:classify(t,s) for s in Strategy}
        self.assertIn("CONVERGING",set(out.values()))
        with self.assertRaises(Refused): DependencyGraph({"a":("b",),"b":("a",)})
