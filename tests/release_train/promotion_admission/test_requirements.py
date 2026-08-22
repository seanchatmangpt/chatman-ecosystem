import unittest
from scripts.release_train.promotion_admission.evidence import Axis,Outcome
from scripts.release_train.promotion_admission.requirements import *
class T(unittest.TestCase):
    def test_profile_requires_every_axis(self):
        p=ReleaseProfile("release",frozenset({Axis.FOCUSED,Axis.REPOSITORY}))
        self.assertEqual(evaluate_profile({Axis.FOCUSED:Outcome.PASS},p),(False,(Axis.REPOSITORY,)))
        self.assertEqual(evaluate_profile({Axis.FOCUSED:Outcome.PASS,Axis.REPOSITORY:Outcome.PASS},p),(True,()))
    def test_fail_cannot_be_accepted(self):
        with self.assertRaises(RequirementRefusal): ReleaseProfile("bad",frozenset({Axis.FOCUSED}),frozenset({Outcome.FAIL}))
if __name__=="__main__": unittest.main()
