import unittest
from scripts.develop_train.evidence_acquisition_runtime.dependency import DependencyGraph
from scripts.develop_train.evidence_acquisition_runtime.standing import bounded_standing,Standing
from scripts.develop_train.evidence_acquisition_runtime.subject import Refusal
class T(unittest.TestCase):
 def test_transitive_failure_dominance(self):
  g=DependencyGraph({'consumer':{'mid'},'mid':{'root'},'root':set()}); self.assertEqual(g.blockers('consumer',{'root':'BUILD_BROKEN'}),('root',)); self.assertEqual(bounded_standing(selected_count=2,dependency_states=['BUILD_BROKEN']),Standing.BUILD_BROKEN)
  with self.assertRaisesRegex(Refusal,'CYCLE'): DependencyGraph({'a':{'b'},'b':{'a'}})
