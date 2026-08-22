import unittest
from scripts.develop_train.recovery_evidence_quorum.dependencies import DependencyGraph
from scripts.develop_train.recovery_evidence_quorum.policy import Standing
from scripts.develop_train.recovery_evidence_quorum.subject import Refused

class TestDependencies(unittest.TestCase):
    def test_transitive_blocker_and_cycle_refusal(self):
        g=DependencyGraph(); g.add('root','mid'); g.add('mid','leaf')
        self.assertEqual(g.blockers('root',{'leaf':Standing.BUILD_BROKEN}),('leaf',))
        with self.assertRaisesRegex(Refused,'DEPENDENCY_CYCLE'): g.add('leaf','root')
