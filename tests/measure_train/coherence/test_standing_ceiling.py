from datetime import datetime, timezone
from scripts.measure_train.coherence.subject import Subject
from scripts.measure_train.coherence.obligation import Axis, Obligation
from scripts.measure_train.coherence.witness import Witness, Outcome
from scripts.measure_train.coherence.coverage import cover
from scripts.measure_train.coherence.coherence import evaluate, Standing
import unittest
S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
def W(axis): return Witness(S,axis,"repo",Outcome.PASS,T,"run")
class TestStanding(unittest.TestCase):
 def test_all_pass_only_partial_alive(self):
  obligations=[Obligation("repo",Axis.REPOSITORY,"repo"),Obligation("receipt",Axis.RECEIPT,"repo")]
  self.assertEqual(evaluate(cover(obligations,[W(Axis.REPOSITORY),W(Axis.RECEIPT)])).standing,Standing.PARTIAL_ALIVE)
 def test_missing_required_unknown(self): self.assertEqual(evaluate(cover([Obligation("repo",Axis.REPOSITORY,"repo")],[])).standing,Standing.UNKNOWN)
if __name__=="__main__": unittest.main()
