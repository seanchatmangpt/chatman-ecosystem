import unittest
from fractions import Fraction
from scripts.develop_train.sequential_acquisition.dependence import SensorDescriptor, IndependenceProof, require_independent
from scripts.develop_train.sequential_acquisition.pareto import frontier
from scripts.develop_train.sequential_acquisition.policy import Candidate
from scripts.develop_train.sequential_acquisition.refusals import Refused

class DependenceParetoCourt(unittest.TestCase):
    def test_independence_requires_structure_and_dominated_candidate_drops(self):
        a=SensorDescriptor("a","fam1","dom1"); b=SensorDescriptor("b","fam2","dom2")
        require_independent(a,b,IndependenceProof(frozenset({("a","b")})))
        with self.assertRaises(Refused): require_independent(a,SensorDescriptor("c","fam1","dom3"),IndependenceProof(frozenset({("a","c")})))
        x=Candidate("x","a",2.0,Fraction(2),Fraction(1),Fraction(1)); y=Candidate("y","b",1.0,Fraction(1),Fraction(2),Fraction(2))
        self.assertEqual([c.candidate_id for c in frontier([x,y])],["x"])
