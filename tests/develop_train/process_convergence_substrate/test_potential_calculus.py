from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.develop_train.process_convergence_substrate import *
from scripts.develop_train.process_convergence_substrate.calculus import velocity,acceleration
from scripts.develop_train.process_convergence_substrate.potential import potential_vector
import unittest

BASE=datetime(2026,8,23,9,0,tzinfo=timezone.utc)
def subj(gen,ch): return SubjectEpoch(f"seanchatmangpt/chatman-ecosystem@{ch*40}",gen)
def epoch(gen,ch,states,minute=0):
    return ClosureEpoch(subj(gen,ch),BASE+timedelta(minutes=minute),tuple(Obligation(k,State[v],Fraction(w,1)) for k,v,w in states))

class TestPotentialCalculus(unittest.TestCase):
    def test_multiple_potentials_and_discrete_calculus(self):
        a=epoch(1,"a",[("a","FAIL",2),("b","BLOCKED",1)],0)
        b=epoch(2,"b",[("a","BLOCKED",2),("b","UNKNOWN",1)],1)
        c=epoch(3,"c",[("a","UNKNOWN",2),("b","PASS",1)],2)
        t=Trajectory((a,b,c))
        self.assertLess(potential_vector(c)[0],potential_vector(a)[0])
        self.assertEqual(len(velocity(t)),2); self.assertEqual(len(acceleration(t)),1)
        self.assertTrue(all(v < 0 for v in velocity(t)))
