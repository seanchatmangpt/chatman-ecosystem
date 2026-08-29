import unittest
from scripts.release_train.regime_current_recovery.dependencies import DependencyGraph
from scripts.release_train.regime_current_recovery.standing import bounded_standing
from scripts.release_train.regime_current_recovery.subject import Refusal
from fixtures import SUBJECT,DEP
class T(unittest.TestCase):
 def test_blocker(self):
  g=DependencyGraph({SUBJECT:(DEP,)}); blockers=g.blockers(SUBJECT,{DEP:'BUILD_BROKEN'}); self.assertEqual(blockers,(DEP,)); self.assertEqual(bounded_standing(['PASS'],'ACCEPT_BOUNDED',2,blockers,True).standing,'BLOCKED')
 def test_fail(self): self.assertEqual(bounded_standing(['PASS','FAIL'],'ACCEPT_BOUNDED',2,(),True).standing,'BUILD_BROKEN')
 def test_cycle(self):
  with self.assertRaisesRegex(Refusal,'DEPENDENCY_CYCLE'): DependencyGraph({SUBJECT:(DEP,),DEP:(SUBJECT,)}).order(SUBJECT)
