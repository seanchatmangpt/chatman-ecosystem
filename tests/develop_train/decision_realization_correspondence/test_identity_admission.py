import unittest
from fractions import Fraction

from scripts.develop_train.decision_realization_correspondence import DecisionPolicy, LossMatrix, Observation, Refused, Subject, admit


class IdentityAdmissionCourt(unittest.TestCase):
    def test_exact_subject_and_generation(self):
        subject = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a" * 40)
        self.assertTrue(subject.key.endswith("a" * 40))
        with self.assertRaises(Refused):
            Subject.parse("seanchatmangpt/chatman-ecosystem@short")
        policy = DecisionPolicy("p", 7, "b" * 64, LossMatrix(Fraction(5), Fraction(1), Fraction(1, 4)))
        obs = Observation("o", 6, "DEFER", None, Fraction(1, 4), Fraction(1), Fraction(), "discovery", "BEAM", "us", "r")
        with self.assertRaises(Refused):
            admit(policy, [obs])


if __name__ == "__main__":
    unittest.main()
