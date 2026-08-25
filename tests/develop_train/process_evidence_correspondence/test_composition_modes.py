import unittest
from scripts.develop_train.process_evidence_correspondence import Evidence, Interval, Provenance, Refused, compose

class TestCompositionModes(unittest.TestCase):
    def test_modes_remain_distinct(self):
        left = Evidence("left", 2, "TRACE", Interval(.7, .9), Provenance("impl-a", "model-a", "domain-a"), "1" * 64)
        right = Evidence("right", 2, "TRACE", Interval(.8, .95), Provenance("impl-b", "model-b", "domain-b"), "2" * 64)
        self.assertAlmostEqual(compose(left, right, "CONSERVATIVE").lo, .5)
        self.assertAlmostEqual(compose(left, right, "INDEPENDENT").lo, .56)

    def test_independence_requires_distinct_provenance(self):
        left = Evidence("left", 2, "TRACE", Interval(.7, .9), Provenance("impl-a", "model-a", "domain-a"), "1" * 64)
        aliased = Evidence("alias", 2, "TRACE", Interval(.8, .95), Provenance("impl-a", "model-c", "domain-c"), "3" * 64)
        with self.assertRaises(Refused):
            compose(left, aliased, "INDEPENDENT")

if __name__ == "__main__": unittest.main()
