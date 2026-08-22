import unittest
from scripts.develop_train.regime_ensemble.detector_vote import DetectorVote, canonical_votes
class TestVote(unittest.TestCase):
    def test_duplicate_detector_refused(self):
        v=DetectorVote("x","f","d",True,1.0)
        with self.assertRaisesRegex(ValueError,"DUPLICATE"): canonical_votes([v,v])
if __name__ == "__main__": unittest.main()
