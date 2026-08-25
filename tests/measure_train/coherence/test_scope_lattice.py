from datetime import datetime, timezone, timedelta
from scripts.measure_train.coherence.subject import Subject, Refusal
from scripts.measure_train.coherence.obligation import Axis, Obligation, Requiredness
from scripts.measure_train.coherence.witness import Witness, Outcome

S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
def W(axis,scope,outcome=Outcome.PASS,source="run",when=T): return Witness(S,axis,scope,outcome,when,source)
import unittest
from scripts.measure_train.coherence.scope import relation, ScopeRelation, satisfies_scope
class TestScope(unittest.TestCase):
 def test_broader_witness_satisfies(self): self.assertTrue(satisfies_scope("repo","repo/python"))
 def test_narrower_witness_does_not_launder(self): self.assertFalse(satisfies_scope("repo/python","repo"))
 def test_disjoint(self): self.assertEqual(relation("repo/python","repo/rust"),ScopeRelation.DISJOINT)
if __name__=="__main__": unittest.main()
