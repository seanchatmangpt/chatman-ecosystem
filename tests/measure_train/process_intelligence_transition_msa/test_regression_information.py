import unittest
from fractions import Fraction
from scripts.measure_train.process_intelligence_transition_msa.regression import regressions
from scripts.measure_train.process_intelligence_transition_msa.information import closure_fraction,realized_closure_gain

class T(unittest.TestCase):
    def test_regression_and_gain(self):
        before=(("a","CI",True,"PASS"),("b","REACTOR",True,"FAIL"))
        after=(("a","CI",True,"FAIL"),("b","REACTOR",True,"PASS"))
        self.assertEqual(regressions(before,after)[0].severity,"HARD")
        self.assertEqual(closure_fraction(before),Fraction(1,2))
        self.assertEqual(realized_closure_gain(before,after),Fraction(0))
