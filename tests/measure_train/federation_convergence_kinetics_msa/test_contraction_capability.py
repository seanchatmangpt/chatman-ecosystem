import unittest
from fractions import Fraction
from scripts.measure_train.federation_convergence_kinetics_msa.contraction import dobrushin
from scripts.measure_train.federation_convergence_kinetics_msa.first_passage import Passage
from scripts.measure_train.federation_convergence_kinetics_msa.capability import on_time_capability

class TestContractionCapability(unittest.TestCase):
    def test_contraction_and_finite_support(self):
        kernel = {"a": {"x": Fraction(1,2), "y": Fraction(1,2)}, "b": {"x": Fraction(1,2), "y": Fraction(1,2)}}
        self.assertEqual(dobrushin(kernel), Fraction(0))
        rows = [Passage(str(i), 1, True, "FIXED") for i in range(20)]
        self.assertEqual(on_time_capability(rows, 2, Fraction(3,4)).state, "CAPABLE")
        self.assertEqual(on_time_capability(rows[:3], 2, Fraction(1,2)).state, "INSUFFICIENT")
