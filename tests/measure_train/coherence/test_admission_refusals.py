from datetime import datetime, timezone, timedelta
from scripts.measure_train.coherence.subject import Subject, Refusal
from scripts.measure_train.coherence.obligation import Axis, Obligation, Requiredness
from scripts.measure_train.coherence.witness import Witness, Outcome

S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
def W(axis,scope,outcome=Outcome.PASS,source="run",when=T): return Witness(S,axis,scope,outcome,when,source)
import unittest
from scripts.measure_train.coherence.admission import admit
class TestAdmission(unittest.TestCase):
 def test_foreign_subject_refuses(self):
  other=Subject("seanchatmangpt/gymact","7ce400e878c1da9b7dc46a81072563ec76ef01f4")
  w=W(Axis.REPOSITORY,"repo"); w=Witness(other,w.axis,w.scope,w.outcome,w.observed_at,w.source)
  with self.assertRaisesRegex(Refusal,"FOREIGN_SUBJECT"): admit(S,[Obligation("repo",Axis.REPOSITORY,"repo")],[w])
 def test_duplicate_obligation_refuses(self):
  o=Obligation("repo",Axis.REPOSITORY,"repo")
  with self.assertRaisesRegex(Refusal,"DUPLICATE_OBLIGATION"): admit(S,[o,o],[])
if __name__=="__main__": unittest.main()
