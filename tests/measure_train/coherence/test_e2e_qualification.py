from datetime import datetime, timezone
from scripts.measure_train.coherence.subject import Subject
from scripts.measure_train.coherence.obligation import Axis, Obligation
from scripts.measure_train.coherence.witness import Witness, Outcome
from scripts.measure_train.coherence.qualifier import qualify
import unittest
S=Subject("seanchatmangpt/chatman-ecosystem","24b39444364cb959f92525453de69981ca511af3")
T=datetime(2026,8,22,9,0,tzinfo=timezone.utc)
def W(axis,scope,outcome,source): return Witness(S,axis,scope,outcome,T,source)
class TestE2E(unittest.TestCase):
 def test_mixed_scope_does_not_launder_repository_failure(self):
  obligations=[Obligation("focused",Axis.FOCUSED,"repo/python"),Obligation("repository",Axis.REPOSITORY,"repo")]
  witnesses=[W(Axis.FOCUSED,"repo/python",Outcome.PASS,"focused"),W(Axis.REPOSITORY,"repo",Outcome.FAIL,"matrix")]
  q=qualify(S,obligations,witnesses,T,{})
  self.assertEqual(q.standing,"BUILD_BROKEN"); self.assertFalse(q.actuation_performed)
 def test_unknown_obligation_prevents_positive_standing(self):
  q=qualify(S,[Obligation("repo",Axis.REPOSITORY,"repo"),Obligation("runtime",Axis.RUNTIME,"repo")],[W(Axis.REPOSITORY,"repo",Outcome.PASS,"matrix")],T,{})
  self.assertEqual(q.standing,"UNKNOWN")
if __name__=="__main__": unittest.main()
