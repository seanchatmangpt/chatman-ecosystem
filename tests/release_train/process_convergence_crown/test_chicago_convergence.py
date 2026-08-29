import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.process_convergence_crown import SubjectEpoch,Obligation,State,ClosureEpoch,Trajectory,DependencyGraph,Strategy,qualify,replay

class ChicagoConvergenceTest(unittest.TestCase):
    def test_repair_progress_cannot_launder_surviving_tls_failure(self):
        t=datetime(2026,8,23,tzinfo=timezone.utc); s0=SubjectEpoch("seanchatmangpt/chatman-ecosystem","a"*40,0,"d"*16); s1=s0.advance("b"*40,"e"*16)
        keys=("reactor","tls","crown")
        e0=ClosureEpoch(s0,t,(Obligation("reactor",State.UNKNOWN),Obligation("tls",State.BUILD_BROKEN),Obligation("crown",State.UNKNOWN)))
        e1=ClosureEpoch(s1,t+timedelta(minutes=1),(Obligation("reactor",State.PASS),Obligation("tls",State.BUILD_BROKEN),Obligation("crown",State.UNKNOWN)))
        q=qualify(Trajectory((e0,e1)),DependencyGraph({"crown":("reactor","tls")}),"crown",Strategy.MINIMAX)
        self.assertEqual(q.standing,"BUILD_BROKEN")
        self.assertEqual(q.blockers,("tls",))
        self.assertEqual(replay(q.receipt,q.receipt.digest()),"REPLAY_MATCH")
        self.assertFalse(q.receipt.actuation_performed)
