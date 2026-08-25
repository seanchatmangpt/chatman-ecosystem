import unittest
from scripts.develop_train.outcome_transport_invariance import *

class ParetoStrata(unittest.TestCase):
    def test_frontier_and_worst_stratum(self):
        candidates = [Candidate("a", .1, .1, -.9, -4), Candidate("b", .2, .2, -.8, -3), Candidate("c", .05, .3, -.7, -2)]
        self.assertIn("a", {item.name for item in frontier(candidates)})
        strata = [Stratum("discovery", "BEAM", "us", "r", .1, 5), Stratum("powl", "WASM", "eu", "x", .3, 5)]
        self.assertEqual(worst(strata).methodology, "powl")

    def test_weak_stratum_refuses(self):
        with self.assertRaises(Refused):
            worst([Stratum("x", "e", "r", "q", .2, 0)])
