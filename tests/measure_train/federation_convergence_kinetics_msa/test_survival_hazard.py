import unittest
from fractions import Fraction
from scripts.measure_train.federation_convergence_kinetics_msa.first_passage import Passage
from scripts.measure_train.federation_convergence_kinetics_msa.survival import on_time_probability
from scripts.measure_train.federation_convergence_kinetics_msa.hazard import nelson_aalen

class TestSurvivalHazard(unittest.TestCase):
    def test_censoring_is_not_failure(self):
        rows = [Passage("a", 1, True, "FIXED"), Passage("b", 2, True, "FIXED"), Passage("c", 2, False, "CENSORED")]
        self.assertEqual(on_time_probability(rows, 1), Fraction(1, 3))
        self.assertEqual(nelson_aalen(rows)[0][3], Fraction(1, 3))
