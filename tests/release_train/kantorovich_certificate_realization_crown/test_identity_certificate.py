import unittest
from fractions import Fraction
from scripts.release_train.kantorovich_certificate_realization_crown import Subject,Certificate,Refused
class T(unittest.TestCase):
    def test_exact_identity_and_certificate(self):
        s=Subject.parse('seanchatmangpt/chatman-ecosystem@'+'a'*40); self.assertTrue(s.identity.endswith('a'*40))
        c=Certificate('b'*64,3,Fraction(2),Fraction(2)); self.assertEqual(c.validate().generation,3)
        with self.assertRaises(Refused): Subject.parse('main')
        with self.assertRaises(Refused): Certificate('x',0,Fraction(1),Fraction(1)).validate()
if __name__=='__main__': unittest.main()
