import unittest
from scripts.develop_train.regime_ensemble.sample import ErrorSample, canonical_samples
from scripts.develop_train.regime_ensemble.subject import Subject

class TestIdentity(unittest.TestCase):
    def test_exact_subject_and_duplicate_sequence_refusal(self):
        s=Subject("o/r","a"*40); self.assertEqual(s.identity,"o/r@"+"a"*40)
        with self.assertRaisesRegex(ValueError,"INEXACT_SUBJECT"): Subject("o/r","abc")
        with self.assertRaisesRegex(ValueError,"DUPLICATE"): canonical_samples([ErrorSample(1,.1,"x"),ErrorSample(1,.2,"x")])
if __name__ == "__main__": unittest.main()
