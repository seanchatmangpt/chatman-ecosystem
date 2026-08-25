import unittest
from fractions import Fraction
from scripts.develop_train.trace_relation_selection import *

class TestChicago(unittest.TestCase):
    def test_calibrated_relations_to_receipt_and_hard_failure(self):
        sha="a"*40; sem="b"*64
        subject=Subject.parse("seanchatmangpt/chatman-ecosystem",sha,sem)
        evs=[
            CalibrationEvidence(Relation.EXACT,7,200,2,8,Fraction(5)),
            CalibrationEvidence(Relation.STUTTER,7,200,3,5,Fraction(3)),
            CalibrationEvidence(Relation.PARTIAL_ORDER,7,200,4,4,Fraction(4)),
            CalibrationEvidence(Relation.ACTIVITY,7,200,1,1,Fraction(1)),
        ]
        frontier=CalibrationFrontier.current(evs)
        mws={r:MetamorphicWitness(r,True,True) for r in Relation}
        os={r:[OracleWitness((r.value+"1").encode().hex().ljust(64,"0")[:64],"1"*64),
               OracleWitness((r.value+"2").encode().hex().ljust(64,"f")[:64],"2"*64)] for r in Relation}
        result=evaluate(subject,frontier,mws,os)
        self.assertEqual(result.standing,Standing.PARTIAL_ALIVE)
        self.assertEqual(result.bundle.strongest,(Relation.EXACT,))
        self.assertIsNotNone(result.receipt)
        self.assertTrue(replay(result.receipt,result.receipt.digest))
        broken=evaluate(subject,frontier,mws,os,hard_failure=True)
        self.assertEqual(broken.standing,Standing.BUILD_BROKEN)
        self.assertIsNone(broken.receipt)
