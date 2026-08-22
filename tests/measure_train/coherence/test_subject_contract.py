from datetime import datetime, timezone, timedelta
from scripts.measure_train.coherence.subject import Subject, Refusal
from scripts.measure_train.coherence.obligation import Axis, Obligation, Requiredness
from scripts.measure_train.coherence.witness import Witness, Outcome

S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
def W(axis,scope,outcome=Outcome.PASS,source="run",when=T): return Witness(S,axis,scope,outcome,when,source)
import unittest
class TestSubject(unittest.TestCase):
 def test_exact(self): self.assertEqual(S.key,"seanchatmangpt/chatman-ecosystem@24b39444364cb959f92525453de69981ca511af3")
 def test_short_refuses(self):
  with self.assertRaisesRegex(Refusal,"INEXACT_SUBJECT"): Subject("seanchatmangpt/chatman-ecosystem","abc")
if __name__=="__main__": unittest.main()
