import unittest
from fixtures import state
from scripts.release_train.replicated_policy_admission.frontier import classify_frontier
class TestFrontier(unittest.TestCase):
    def test_historical_and_current(self):
        f=classify_frontier([state('a',clock={'a':1}),state('b',clock={'a':2})]); self.assertEqual(f.historical,('a',)); self.assertEqual(f.current,('b',)); self.assertFalse(f.concurrent)
    def test_concurrency_visible(self): self.assertTrue(classify_frontier([state('a',clock={'a':1}),state('b',clock={'b':1})]).concurrent)
