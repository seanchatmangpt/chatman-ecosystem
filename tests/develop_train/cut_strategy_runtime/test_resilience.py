import unittest
from scripts.develop_train.cut_strategy_runtime.resilience import deterministic_advancement
class ResilienceCourt(unittest.TestCase):
    def test_seeded_advancement_replays(self):
        repos=('a/r','b/r','c/r')
        self.assertEqual(deterministic_advancement(repos,seed=42,count=5), deterministic_advancement(repos,seed=42,count=5))
        self.assertEqual(len(deterministic_advancement(repos,seed=42,count=5)),5)
if __name__ == '__main__': unittest.main()
