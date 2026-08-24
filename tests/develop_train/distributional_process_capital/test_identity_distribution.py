import unittest
from fractions import Fraction
from scripts.develop_train.distributional_process_capital.errors import Refused
from scripts.develop_train.distributional_process_capital.subject import Subject
from scripts.develop_train.distributional_process_capital.distribution import Distribution
class IdentityDistributionCourt(unittest.TestCase):
    def test_exact_subject_and_normalization(self):
        s=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40+"#"+"b"*64)
        self.assertEqual(s.sha,"a"*40)
        p=Distribution.from_mapping({"a":3,"b":1})
        self.assertEqual(sum(q for _,q in p.mass),Fraction(1))
    def test_refusals(self):
        with self.assertRaises(Refused): Subject.parse("bad")
        with self.assertRaises(Refused): Distribution.from_mapping({"a":0})
        with self.assertRaises(Refused): Distribution.from_mapping({"a":-1,"b":2})
if __name__=="__main__": unittest.main()
