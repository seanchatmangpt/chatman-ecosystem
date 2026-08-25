import unittest
from fractions import Fraction
from scripts.develop_train.trace_relation_selection import *

class TestFrontierOracle(unittest.TestCase):
    def test_split_and_alias_refuse(self):
        a=CalibrationEvidence(Relation.EXACT,2,100,1,1,Fraction(1))
        b=CalibrationEvidence(Relation.EXACT,2,100,2,1,Fraction(1))
        with self.assertRaises(Refused):
            CalibrationFrontier.current([a,b])
        with self.assertRaises(Refused):
            require_independent([OracleWitness("a","m1"),OracleWitness("a","m2")])
