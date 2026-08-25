import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.release_train.process_convergence_crown import SubjectEpoch,Obligation,State,ClosureEpoch,Trajectory,potential_vector
from scripts.release_train.process_convergence_crown.calculus import velocity,acceleration
from scripts.release_train.process_convergence_crown.witness import lyapunov_nonincrease
from scripts.release_train.process_convergence_crown.cusum import Cusum

class CalculusWitnessTest(unittest.TestCase):
    def _trajectory(self):
        t=datetime(2026,8,23,tzinfo=timezone.utc); s=SubjectEpoch("o/r","a"*40,0,"d"*16)
        es=[]
        for i,state in enumerate((State.BUILD_BROKEN,State.UNKNOWN,State.PASS)):
            if i: s=s.advance(chr(97+i)*40,"d"*16)
            es.append(ClosureEpoch(s,t+timedelta(minutes=i),(Obligation("rail",state,Fraction(2,1)),)))
        return Trajectory(tuple(es))
    def test_debt_velocity_and_lyapunov(self):
        tr=self._trajectory(); self.assertEqual(velocity(tr),(Fraction(-6,1),Fraction(-4,1))); self.assertTrue(lyapunov_nonincrease(tr)); self.assertEqual(acceleration(tr),(Fraction(2,1),))
    def test_cusum_detects_shift(self):
        c=Cusum(threshold=Fraction(1,1))
        c=c.advance(Fraction(2,1)); self.assertTrue(c.changed)
