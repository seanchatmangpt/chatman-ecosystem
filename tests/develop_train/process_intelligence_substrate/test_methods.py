import unittest
from fractions import Fraction
from scripts.develop_train.process_intelligence_substrate import Candidate, Transition, conformance_score, next_activity, pareto, simulate
from scripts.develop_train.process_intelligence_substrate.errors import Refused

class MethodsTest(unittest.TestCase):
    def test_conformance_simulation_prediction_optimization(self):
        self.assertEqual(conformance_score(("A","B"), ("A","B")), Fraction(1,1))
        state, executed = simulate("s0", (Transition("s0","A","s1"), Transition("s1","B","s2")), ("A","B"), 2)
        self.assertEqual((state, executed), ("s2", ("A","B")))
        preds = next_activity((("A","B"),("A","B"),("A","C")), ("A",), 2)
        self.assertEqual(sum((p.probability for p in preds), Fraction()), Fraction(1,1))
        frontier = pareto((Candidate("x", Fraction(3,4), Fraction(2), Fraction(2)), Candidate("y", Fraction(1,2), Fraction(3), Fraction(3))))
        self.assertEqual(tuple(c.name for c in frontier), ("x",))
        with self.assertRaises(Refused): simulate("s0", (), ("A",), 1)

if __name__ == "__main__": unittest.main()
