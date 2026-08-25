import unittest
from fractions import Fraction
from scripts.develop_train.validation_independence_control import Calibration, Dependence, Evidence, EvidenceGraph, Provenance, Refused, ancestry_overlap, effective_independence, current

class DependenceCalibrationCourt(unittest.TestCase):
    def setUp(self):
        self.graph = EvidenceGraph((Evidence("a",4,(),1), Evidence("b",4,(),1), Evidence("c",4,("a",),1)))
        self.pa = Provenance("impl-a","model-a","domain-a"); self.pb = Provenance("impl-b","model-b","domain-b")

    def test_zero_overlap_and_empirical_zero_are_required(self):
        self.assertEqual(ancestry_overlap(self.graph,"a","b"), Fraction(0))
        d=Dependence(Fraction(0),Fraction(0),Fraction(0),4,"d"*64)
        self.assertTrue(effective_independence(self.graph,"a","b",self.pa,self.pb,d))
        shared=Dependence(ancestry_overlap(self.graph,"a","c"),Fraction(0),Fraction(0),4,"e"*64)
        with self.assertRaises(Refused) as overlap: effective_independence(self.graph,"a","c",self.pa,self.pb,shared)
        self.assertEqual(overlap.exception.code,"EMPIRICAL_DEPENDENCE")
        with self.assertRaises(Refused): effective_independence(self.graph,"a","b",self.pa,self.pb,Dependence(Fraction(0),Fraction(1,10),Fraction(0),4,"f"*64))

    def test_calibration_frontier_is_exact_and_current(self):
        old=Calibration(3,"1"*64,30,Fraction(9,10),Fraction(1,10),Fraction(1,4),Fraction(1,20),Fraction(1,20))
        new=Calibration(4,"2"*64,40,Fraction(19,20),Fraction(1,20),Fraction(1,5),Fraction(1,40),Fraction(1,40))
        self.assertIs(current((old,new)),new)
        divergent=Calibration(4,"3"*64,40,Fraction(19,20),Fraction(1,20),Fraction(1,5),Fraction(1,40),Fraction(1,40))
        with self.assertRaises(Refused) as split: current((new,divergent))
        self.assertEqual(split.exception.code,"DIVERGENT_CURRENT_CALIBRATION")

if __name__ == "__main__": unittest.main()
