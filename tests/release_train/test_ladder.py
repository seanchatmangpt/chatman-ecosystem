import unittest
from scripts.release_train.ladder import Gate,evaluate

class LadderTests(unittest.TestCase):
    def test_full_ladder_is_alive(self):
        names=("narrow","compile","unit","property","integration","e2e","replay","negative","security","exact_head_ci")
        self.assertEqual(evaluate([Gate(n,"success") for n in names]),"ALIVE")
    def test_partial_does_not_overclaim(self):
        self.assertEqual(evaluate([Gate("narrow","success")]),"PARTIAL_ALIVE")
    def test_failure_breaks_build(self):
        self.assertEqual(evaluate([Gate("narrow","success"),Gate("compile","failure")]),"BUILD_BROKEN")
