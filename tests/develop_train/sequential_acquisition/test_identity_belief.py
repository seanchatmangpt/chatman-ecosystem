import unittest
from fractions import Fraction
from scripts.develop_train.sequential_acquisition.subject import Subject
from scripts.develop_train.sequential_acquisition.belief import BeliefState
from scripts.develop_train.sequential_acquisition.refusals import Refused

class IdentityBeliefCourt(unittest.TestCase):
    def test_exact_subject_and_normalized_belief(self):
        Subject("seanchatmangpt/chatman-ecosystem@" + "a"*40)
        b = BeliefState(0, {"good": Fraction(1,2), "bad": Fraction(1,2)})
        self.assertEqual(b.confidence, Fraction(1,2))
        with self.assertRaises(Refused): Subject("repo@short")
        with self.assertRaises(Refused): BeliefState(0, {"x": Fraction(2,3)})
