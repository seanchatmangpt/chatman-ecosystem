import unittest
from fractions import Fraction
from scripts.release_train.compositional_robustness_admission import *
class T(unittest.TestCase):
    def test_exact_current_composition_is_bounded_and_receipted(self):
        s=Subject("seanchatmangpt/chatman-ecosystem","a"*40); cal=BoundCalibration(10,Fraction(19,20),Fraction(1),3,"f"*64)
        e1=EvidenceIdentity("ips","1"*64,"2"*64); e2=EvidenceIdentity("dr","3"*64,"4"*64)
        b1=PolicyBound(PolicyIdentity(7,"b"*64),Interval(Fraction(2),Fraction(3)),Fraction(3),1,1,e1,3,"f"*64)
        b2=PolicyBound(PolicyIdentity(7,"c"*64),Interval(Fraction(3,2),Fraction(5,2)),Fraction(4),1,1,e2,3,"f"*64)
        q=qualify(subject=s,bounds=(b1,b2),calibrations=CalibrationFrontier((cal,)),independence=IndependenceProof(frozenset({("dr","ips")})),shift_radius=Fraction(1,20),lipschitz=1,compatibility=CompatibilityHypergraph(frozenset()),dependency=DependencyGraph({"release":()},{"release":"PARTIAL_ALIVE"}),root="release",strategy=Strategy.MAX_LOWER)
        self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertFalse(q.receipt.actuation_performed); self.assertTrue(replay(q.receipt,q.receipt.digest))
    def test_red_dependency_blocks(self):
        s=Subject("seanchatmangpt/chatman-ecosystem","a"*40); cal=BoundCalibration(10,Fraction(19,20),Fraction(1),3,"f"*64)
        e1=EvidenceIdentity("ips","1"*64,"2"*64); b1=PolicyBound(PolicyIdentity(7,"b"*64),Interval(2,3),Fraction(3),1,1,e1,3,"f"*64)
        q=qualify(subject=s,bounds=(b1,),calibrations=CalibrationFrontier((cal,)),independence=IndependenceProof(frozenset()),shift_radius=Fraction(0),lipschitz=0,compatibility=CompatibilityHypergraph(frozenset()),dependency=DependencyGraph({"release":("dep",)},{"dep":"BUILD_BROKEN"}),root="release",strategy=Strategy.MAX_LOWER)
        self.assertEqual(q.standing,"BLOCKED"); self.assertIsNone(q.selected)
