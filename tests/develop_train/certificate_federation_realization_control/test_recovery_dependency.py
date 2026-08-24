import unittest
from scripts.develop_train.certificate_federation_realization_control import *
class RecoveryDependency(unittest.TestCase):
    def test_recovery_distinction(self):
        self.assertEqual(classify(Relation.CENSORED,Relation.EXACT),Recovery.OBSERVABILITY_RECOVERED)
        self.assertEqual(classify(Relation.DIVERGED,Relation.EXACT),Recovery.SEMANTIC_REPAIR)
    def test_dependency_cycle_and_hard_blocker(self):
        with self.assertRaises(Refused): blockers({"a":["b"],"b":["a"]},{})
        self.assertEqual(blockers({"a":["b"],"b":[]},{"b":"BUILD_BROKEN"}),frozenset({"b"}))
if __name__=="__main__": unittest.main()
