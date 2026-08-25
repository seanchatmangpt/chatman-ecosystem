import unittest
from scripts.develop_train.process_evidence_correspondence import *

class TestDistributionFailure(unittest.TestCase):
    def test_distribution_and_failure_dominance(self):
        cert="c"*64
        witnesses=[RegionWitness("host-a","region-a",4,10,20,True,cert,"sem"),RegionWitness("host-b","region-b",4,11,21,True,cert,"sem")]
        self.assertTrue(require_distribution(witnesses,15))
        self.assertTrue(require_failure_worlds(REQUIRED_FAILURES))
        self.assertEqual(combine_standing(["PARTIAL_ALIVE","ALIVE"]),"PARTIAL_ALIVE")
        self.assertEqual(combine_standing(["PARTIAL_ALIVE","BUILD_BROKEN"]),"BUILD_BROKEN")
        bad=[RegionWitness("host-a","region-a",4,10,20,False,cert,"sem"),RegionWitness("host-b","region-b",4,11,21,True,cert,"sem")]
        with self.assertRaises(Refused):
            require_distribution(bad,15)

if __name__ == "__main__": unittest.main()
