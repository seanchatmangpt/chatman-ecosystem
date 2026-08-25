import unittest
from fractions import Fraction
from scripts.release_train.process_convergence_crown import DependencyGraph,State
from scripts.release_train.process_convergence_crown.frontier import Candidate,pareto
from scripts.release_train.process_convergence_crown.refusal import Refused

class DependencyStrategyTest(unittest.TestCase):
    def test_transitive_blocking_cut(self):
        g=DependencyGraph({"crown":("runtime",),"runtime":("tls",)})
        self.assertEqual(g.blocking_cut("crown",{"tls":State.BUILD_BROKEN}),("tls",))
    def test_cycle_refuses(self):
        with self.assertRaises(Refused): DependencyGraph({"a":("b",),"b":("a",)}).validate()
    def test_pareto_preserves_nondominated(self):
        a=Candidate("a",Fraction(1),1,0,0); b=Candidate("b",Fraction(2),2,1,1); c=Candidate("c",Fraction(0),3,0,0)
        self.assertEqual({x.name for x in pareto((a,b,c))},{"a","c"})
