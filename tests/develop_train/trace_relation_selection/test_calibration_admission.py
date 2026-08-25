import unittest
from fractions import Fraction
from scripts.develop_train.trace_relation_selection import *
from scripts.develop_train.trace_relation_selection.admission import admit_relation

class TestCalibrationAdmission(unittest.TestCase):
    def test_sparse_and_high_false_equivalence_refuse(self):
        ev = CalibrationEvidence(Relation.ACTIVITY, 1, 10, 0, 0, Fraction(1))
        fr = CalibrationFrontier.current([ev])
        mw = MetamorphicWitness(Relation.ACTIVITY, True, True)
        oracles=[OracleWitness("a"*64,"b"*64),OracleWitness("c"*64,"d"*64)]
        with self.assertRaises(Refused):
            admit_relation(Relation.ACTIVITY, fr, mw, oracles)
        bad = CalibrationEvidence(Relation.ACTIVITY, 2, 100, 30, 1, Fraction(1))
        with self.assertRaises(Refused):
            admit_relation(Relation.ACTIVITY, CalibrationFrontier.current([bad]), mw, oracles)
