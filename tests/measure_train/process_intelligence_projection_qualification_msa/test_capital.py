import unittest
from fractions import Fraction
from scripts.measure_train.process_intelligence_projection_qualification_msa.subject import Subject
from scripts.measure_train.process_intelligence_projection_qualification_msa.projection import Projection
from scripts.measure_train.process_intelligence_projection_qualification_msa.capital import effective_capital
class T(unittest.TestCase):
    def test_duplicate_capital_collapses(self):
        s=Subject('o/r','a'*40,'b'*64); rows=[Projection(str(i),s,'DISCOVERY','e','r','root','b'*64,'c'*64) for i in range(3)]
        self.assertEqual(effective_capital(rows),Fraction(1,3))
