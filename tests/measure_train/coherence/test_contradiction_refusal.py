from datetime import datetime, timezone
from scripts.measure_train.coherence.subject import Subject, Refusal
from scripts.measure_train.coherence.obligation import Axis, Obligation
from scripts.measure_train.coherence.witness import Witness, Outcome
from scripts.measure_train.coherence.admission import admit
import unittest
S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
def W(outcome): return Witness(S,Axis.REPOSITORY,"repo",outcome,T,"same-run")
class TestContradiction(unittest.TestCase):
 def test_same_sensor_conflict_refuses(self):
  with self.assertRaisesRegex(Refusal,"CONTRADICTORY_WITNESS"):
   admit(S,[Obligation("repo",Axis.REPOSITORY,"repo")],[W(Outcome.PASS),W(Outcome.FAIL)])
if __name__=="__main__": unittest.main()
