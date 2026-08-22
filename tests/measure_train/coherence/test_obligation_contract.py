from datetime import datetime, timezone, timedelta
from scripts.measure_train.coherence.subject import Subject, Refusal
from scripts.measure_train.coherence.obligation import Axis, Obligation, Requiredness
from scripts.measure_train.coherence.witness import Witness, Outcome

S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
def W(axis,scope,outcome=Outcome.PASS,source="run",when=T): return Witness(S,axis,scope,outcome,when,source)
import unittest
class TestObligation(unittest.TestCase):
 def test_required_default(self): self.assertEqual(Obligation("repo-ci",Axis.REPOSITORY,"repo").requiredness,Requiredness.REQUIRED)
 def test_bad_id_refuses(self):
  with self.assertRaisesRegex(Refusal,"INVALID_OBLIGATION_ID"): Obligation("repo ci",Axis.REPOSITORY,"repo")
if __name__=="__main__": unittest.main()
