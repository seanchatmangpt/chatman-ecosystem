import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.process_convergence_crown import SubjectEpoch,Obligation,State,ClosureEpoch,Trajectory
from scripts.release_train.process_convergence_crown.refusal import Refused

class IdentityTrajectoryTest(unittest.TestCase):
    def test_contiguous_exact_trajectory(self):
        a=SubjectEpoch("seanchatmangpt/chatman-ecosystem","a"*40,1,"d"*16)
        b=a.advance("b"*40,"e"*16)
        t0=datetime(2026,8,23,tzinfo=timezone.utc)
        tr=Trajectory((ClosureEpoch(a,t0,(Obligation("crown",State.UNKNOWN),)),ClosureEpoch(b,t0+timedelta(minutes=1),(Obligation("crown",State.PASS),))))
        self.assertEqual(tr.current.subject.generation,2)
    def test_universe_drift_refuses(self):
        a=SubjectEpoch("o/r","a"*40,1,"d"*16); b=a.advance("b"*40,"e"*16); t=datetime.now(timezone.utc)
        with self.assertRaises(Refused): Trajectory((ClosureEpoch(a,t,(Obligation("a",State.PASS),)),ClosureEpoch(b,t+timedelta(seconds=1),(Obligation("b",State.PASS),))))
