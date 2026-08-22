import unittest
from fractions import Fraction
from scripts.develop_train.recovery_evidence_quorum.diversity import effective_source_diversity

class TestDiversity(unittest.TestCase):
    def test_inverse_simpson_exact(self):
        self.assertEqual(effective_source_diversity((('a','b'),('c',))), Fraction(9,5))
        self.assertEqual(effective_source_diversity(()), Fraction(0,1))
