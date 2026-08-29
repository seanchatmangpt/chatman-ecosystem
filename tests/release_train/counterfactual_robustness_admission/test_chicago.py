from datetime import datetime,timezone
from fractions import Fraction as F
import unittest
from scripts.release_train.counterfactual_robustness_admission import *
NOW=datetime(2026,8,23,5,35,tzinfo=timezone.utc)
SUB=Subject("seanchatmangpt/chatman-ecosystem","a"*40)
POL=PolicyIdentity("p",7,"b"*64)
def rows(): return admit_log([LoggedOutcome("e1",F(1,2),F(1,2),F(4,5),F(3,4),NOW),LoggedOutcome("e2",F(1,2),F(1,2),F(3,5),F(2,3),NOW),LoggedOutcome("e3",F(1,2),F(1,2),F(7,10),F(7,10),NOW)])
def cals(): return (Calibration("ips",2,"1"*64,10,F(1,10),"2"*64),Calibration("dr",2,"3"*64,10,F(1,12),"4"*64,"5"*64))
class T(unittest.TestCase):
 def test_robust_release_admission_and_blocker(self):
  cand=(Candidate(POL.digest,Interval(F(2,5),F(3,5)),F(2)),Candidate("c"*64,Interval(F(1,2),F(9,10)),F(4)))
  q=qualify(subject=SUB,current_policy=POL,calibrations=cals(),proof_pairs={("ips","dr")},logs=rows(),candidates=cand,strategy=RobustStrategy.HOLD)
  self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertEqual(q.selected_policy_digest,POL.digest); self.assertTrue(replay(q.receipt)); self.assertFalse(q.receipt.body["actuation_performed"]); self.assertEqual(q.phases,("VERIFY","CONSTRUCT"))
  g=DependencyGraph({SUB.repo:("dep",),"dep":()},{"dep":"BUILD_BROKEN"}); q2=qualify(subject=SUB,current_policy=POL,calibrations=cals(),proof_pairs={("ips","dr")},logs=rows(),candidates=cand,strategy=RobustStrategy.HOLD,dependencies=g); self.assertEqual(q2.standing,"BLOCKED")
