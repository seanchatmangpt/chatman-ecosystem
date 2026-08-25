import unittest
from fractions import Fraction
from scripts.develop_train.validation_independence_control import Candidate, CompositionMode, Dependence, Evidence, EvidenceGraph, Interval, Provenance, Refused, Strategy, ValidatorWitness, compose, pareto, select

class ValidatorCompositionCourt(unittest.TestCase):
    def setUp(self):
        self.graph=EvidenceGraph((Evidence("ea",8,(),1),Evidence("eb",8,(),1)))
        self.va=ValidatorWitness("va","1"*64,Provenance("ia","ma","da"),"ea")
        self.vb=ValidatorWitness("vb","2"*64,Provenance("ib","mb","db"),"eb")
        self.dep=Dependence(Fraction(0),Fraction(0),Fraction(0),8,"3"*64)

    def test_conservative_and_independence_modes_do_not_collapse(self):
        a,b=Interval(Fraction(1,2),Fraction(4,5)),Interval(Fraction(3,5),Fraction(9,10))
        conservative=compose(a,b,CompositionMode.CONSERVATIVE)
        independent=compose(a,b,CompositionMode.INDEPENDENCE_QUALIFIED,graph=self.graph,a_validator=self.va,b_validator=self.vb,dependence=self.dep)
        self.assertNotEqual(conservative,independent)
        self.assertEqual(independent.lo,Fraction(3,10)); self.assertEqual(independent.hi,Fraction(18,25))

    def test_alias_and_selector_monoculture_refuse_or_diverge(self):
        a=Interval(Fraction(1,2),Fraction(4,5))
        with self.assertRaises(Refused): compose(a,a,CompositionMode.INDEPENDENCE_QUALIFIED,graph=self.graph,a_validator=self.va,b_validator=self.va,dependence=self.dep)
        cs=(Candidate("coverage",Fraction(99,100),Fraction(2,5),Fraction(0),Fraction(1,100),8),Candidate("width",Fraction(9,10),Fraction(1,10),Fraction(0),Fraction(1,20),2),Candidate("overlap",Fraction(23,25),Fraction(1,5),Fraction(0),Fraction(3,100),4))
        f=pareto(cs); self.assertGreaterEqual(len(f),2)
        self.assertGreaterEqual(len({select(f,s).name for s in Strategy}),2)

if __name__ == "__main__": unittest.main()
