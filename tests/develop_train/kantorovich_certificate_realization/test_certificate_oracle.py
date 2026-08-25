import unittest
from fractions import Fraction
from scripts.develop_train.kantorovich_certificate_realization import *
from test_identity_admission import CERT, observation

class CertificateOracle(unittest.TestCase):
    def test_exact_certificate_and_oracle(self):
        self.assertTrue(measure_feasibility(CERT).exact)
        result = differential(CERT, [observation(i) for i in range(4)])
        self.assertEqual(result.max_absolute_gap, Fraction(0))

    def test_nonzero_gap_is_not_exact(self):
        bad = Certificate("d"*64, 7, Fraction(3,2), Fraction(7,5), Fraction(0), Fraction(0))
        self.assertFalse(measure_feasibility(bad).exact)

if __name__ == "__main__": unittest.main()
