import unittest
from scripts.develop_train.cut_strategy_runtime.identity import Refusal
from scripts.develop_train.cut_strategy_runtime.topology import DependencyGraph
class TopologyCourt(unittest.TestCase):
    def test_cycle_refuses_and_closure_is_transitive(self):
        g=DependencyGraph({'release':('api',),'api':('db',),'db':()})
        self.assertEqual(g.closure('release'), ('api','db','release'))
        with self.assertRaisesRegex(Refusal, 'DEPENDENCY_CYCLE'):
            DependencyGraph({'a':('b',),'b':('a',)})
if __name__ == '__main__': unittest.main()
