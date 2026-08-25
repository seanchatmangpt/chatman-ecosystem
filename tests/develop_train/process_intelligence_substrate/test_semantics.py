import unittest
from scripts.develop_train.process_intelligence_substrate import Precedence, PowlModel, PowlNode, ReactorStep, topological_order, validate_precedence
from scripts.develop_train.process_intelligence_substrate.errors import Refused

class SemanticsTest(unittest.TestCase):
    def test_declarative_procedural_powl_differential(self):
        self.assertTrue(validate_precedence(("A","B"), (Precedence("A","B"),)))
        self.assertFalse(validate_precedence(("B","A"), (Precedence("A","B"),)))
        self.assertEqual(topological_order((ReactorStep("A"), ReactorStep("B", ("A",)))), ("A","B"))
        model = PowlModel("A", (PowlNode("A", ("B",)), PowlNode("B", ("A",))), 4)
        self.assertEqual(model.reachable(), frozenset({"A","B"}))
        with self.assertRaises(Refused):
            topological_order((ReactorStep("A", ("B",)), ReactorStep("B", ("A",))))

if __name__ == "__main__": unittest.main()
