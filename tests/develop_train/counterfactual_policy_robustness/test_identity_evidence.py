import unittest
from fractions import Fraction
from scripts.develop_train.counterfactual_policy_robustness.errors import Refused
from scripts.develop_train.counterfactual_policy_robustness.subject import Subject
from scripts.develop_train.counterfactual_policy_robustness.evidence import LoggedOutcome,admit_log
class TestIdentityEvidence(unittest.TestCase):
    def test_exact_subject_and_unique_log(self):
        s=Subject('seanchatmangpt/chatman-ecosystem@'+'a'*40); self.assertTrue(s.value.endswith('a'*40)); row=LoggedOutcome('c1','A',Fraction(1),Fraction(1,2),Fraction(1,2)); self.assertEqual(admit_log([row]),(row,))
        with self.assertRaisesRegex(Refused,'INEXACT'): Subject('main')
        with self.assertRaisesRegex(Refused,'DUPLICATE'): admit_log([row,row])
