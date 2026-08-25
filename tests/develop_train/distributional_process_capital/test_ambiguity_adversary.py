import unittest
from fractions import Fraction
from scripts.develop_train.distributional_process_capital.errors import Refused
from scripts.develop_train.distributional_process_capital.distribution import Distribution
from scripts.develop_train.distributional_process_capital.ambiguity import AmbiguitySet,Kind
from scripts.develop_train.distributional_process_capital.adversary import tv_extremes
from scripts.develop_train.distributional_process_capital.expectation import worst_case
class AmbiguityCourt(unittest.TestCase):
    def test_worst_case_witness_is_admitted(self):
        p=Distribution.from_mapping({"a":3,"b":1}); amb=AmbiguitySet(p,Kind.TV,Fraction(1,4))
        candidates=tv_extremes(p,Fraction(1,4))
        self.assertTrue(all(amb.contains(c) for c in candidates))
        result=worst_case(amb,candidates,{"a":0,"b":1})
        self.assertIn(result.witness,candidates)
    def test_negative_radius_refuses(self):
        p=Distribution.from_mapping({"a":1})
        with self.assertRaises(Refused): AmbiguitySet(p,Kind.TV,Fraction(-1))
if __name__=="__main__": unittest.main()
