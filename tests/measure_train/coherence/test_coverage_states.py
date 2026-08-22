from datetime import datetime, timezone
from scripts.measure_train.coherence.subject import Subject
from scripts.measure_train.coherence.obligation import Axis, Obligation
from scripts.measure_train.coherence.witness import Witness, Outcome
from scripts.measure_train.coherence.coverage import cover, CoverageState
import unittest
S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
def W(outcome=Outcome.PASS,source="run"): return Witness(S,Axis.REPOSITORY,"repo",outcome,T,source)
class TestCoverage(unittest.TestCase):
 def test_missing_is_unknown(self): self.assertEqual(cover([Obligation("repo",Axis.REPOSITORY,"repo")],[])[0].state,CoverageState.UNKNOWN)
 def test_fail_dominates_pass(self): self.assertEqual(cover([Obligation("repo",Axis.REPOSITORY,"repo")],[W(Outcome.PASS,"a"),W(Outcome.FAIL,"b")])[0].state,CoverageState.FAILED)
 def test_unsupported_distinct(self):
  w=W(Outcome.UNSUPPORTED); w=Witness(S,Axis.RUNTIME,"repo",w.outcome,w.observed_at,w.source)
  self.assertEqual(cover([Obligation("runtime",Axis.RUNTIME,"repo")],[w])[0].state,CoverageState.UNSUPPORTED)
if __name__=="__main__": unittest.main()
