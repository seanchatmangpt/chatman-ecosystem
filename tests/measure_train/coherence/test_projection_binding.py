from datetime import datetime, timezone
from scripts.measure_train.coherence.subject import Subject
from scripts.measure_train.coherence.obligation import Axis, Obligation
from scripts.measure_train.coherence.witness import Witness, Outcome
from scripts.measure_train.coherence.coverage import cover
from scripts.measure_train.coherence.projection import to_ocel
import unittest
S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
class TestProjection(unittest.TestCase):
 def test_subject_and_scope_preserved(self):
  o=[Obligation("repo",Axis.REPOSITORY,"repo")]; w=[Witness(S,Axis.REPOSITORY,"repo",Outcome.PASS,T,"run")]; events=to_ocel(S,w,cover(o,w))
  self.assertEqual(events[0]["subject"],S.key); self.assertEqual(events[0]["scope"],"repo")
if __name__=="__main__": unittest.main()
