import unittest
from fractions import Fraction
from scripts.release_train.kantorovich_certificate_realization_crown import Certificate,Observation,Refused
from scripts.release_train.kantorovich_certificate_realization_crown.admission import admit
from scripts.release_train.kantorovich_certificate_realization_crown.consequence import evaluate
class T(unittest.TestCase):
    def test_duplicate_foreign_and_false_safe(self):
        c=Certificate('b'*64,1,Fraction(1),Fraction(1)); o=Observation('1','b'*64,1,Fraction(1),Fraction(2),Fraction(1),'i','m','r','discovery','BEAM','us','node')
        self.assertEqual(evaluate((o,)).false_safe_rate,1)
        with self.assertRaises(Refused): admit(c,(o,o))
        bad=Observation('2','c'*64,1,Fraction(1),Fraction(1),Fraction(1),'i','m','r','discovery','BEAM','us','node')
        with self.assertRaises(Refused): admit(c,(bad,))
if __name__=='__main__': unittest.main()
