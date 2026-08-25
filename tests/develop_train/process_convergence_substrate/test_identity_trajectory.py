from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.develop_train.process_convergence_substrate import *
import unittest

BASE=datetime(2026,8,23,9,0,tzinfo=timezone.utc)
def subj(gen,ch): return SubjectEpoch(f"seanchatmangpt/chatman-ecosystem@{ch*40}",gen)
def epoch(gen,ch,states,minute=0):
    return ClosureEpoch(subj(gen,ch),BASE+timedelta(minutes=minute),tuple(Obligation(k,State[v],Fraction(w,1)) for k,v,w in states))

class TestIdentityTrajectory(unittest.TestCase):
    def test_exact_subject_and_contiguous_universe(self):
        a=epoch(1,"a",[("semantic","PASS",2),("ci","FAIL",3)],0)
        b=epoch(2,"b",[("semantic","PASS",2),("ci","BLOCKED",3)],1)
        t=Trajectory((a,b)); self.assertEqual(t.current.subject.generation,2)
        with self.assertRaises(Refused): SubjectEpoch("bad",0)
        c=ClosureEpoch(subj(4,"c"),BASE+timedelta(minutes=2),b.obligations)
        with self.assertRaises(Refused): Trajectory((a,c))
    def test_universe_drift_refuses(self):
        a=epoch(1,"a",[("semantic","PASS",1),("ci","FAIL",1)],0)
        b=epoch(2,"b",[("semantic","PASS",1),("new","PASS",1)],1)
        with self.assertRaises(Refused): Trajectory((a,b))
