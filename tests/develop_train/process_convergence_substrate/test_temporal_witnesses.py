from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.develop_train.process_convergence_substrate import *
from scripts.develop_train.process_convergence_substrate.oscillation import oscillating_keys
from scripts.develop_train.process_convergence_substrate.hazard import hazards
from scripts.develop_train.process_convergence_substrate.witness import lyapunov_witness
from scripts.develop_train.process_convergence_substrate.changepoint import Cusum
import unittest

BASE=datetime(2026,8,23,9,0,tzinfo=timezone.utc)
def subj(gen,ch): return SubjectEpoch(f"seanchatmangpt/chatman-ecosystem@{ch*40}",gen)
def epoch(gen,ch,states,minute=0):
    return ClosureEpoch(subj(gen,ch),BASE+timedelta(minutes=minute),tuple(Obligation(k,State[v],Fraction(w,1)) for k,v,w in states))

class TestTemporalWitnesses(unittest.TestCase):
    def test_oscillation_hazard_lyapunov_and_cusum(self):
        a=epoch(1,"a",[("ci","PASS",1),("tls","FAIL",1)],0)
        b=epoch(2,"b",[("ci","FAIL",1),("tls","BLOCKED",1)],1)
        c=epoch(3,"c",[("ci","PASS",1),("tls","UNKNOWN",1)],2)
        t=Trajectory((a,b,c))
        self.assertIn("ci",oscillating_keys(t))
        h=hazards(t); self.assertGreater(h.discharge,Fraction(0,1)); self.assertGreater(h.regression,Fraction(0,1))
        self.assertFalse(lyapunov_witness(t).nonincreasing)
        q=Cusum(Fraction(2,1)); q=q.advance(Fraction(1,1)).advance(Fraction(1,1)); self.assertTrue(q.changed)
