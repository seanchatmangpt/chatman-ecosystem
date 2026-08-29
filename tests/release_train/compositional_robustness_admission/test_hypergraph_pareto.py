import unittest
from fractions import Fraction
from scripts.release_train.compositional_robustness_admission import *
from scripts.release_train.compositional_robustness_admission.pareto import frontier
class T(unittest.TestCase):
    def _b(self,d,l,u,cost):
        return PolicyBound(PolicyIdentity(1,d*64),Interval(Fraction(l),Fraction(u)),Fraction(2),Fraction(cost),Fraction(1),EvidenceIdentity(d,d*64,(d.upper())*64),1,"f"*64)
    def test_forbidden_hyperedge_and_pareto(self):
        h=CompatibilityHypergraph(frozenset({frozenset(("a"*64,"b"*64))})); self.assertFalse(h.feasible(("a"*64,"b"*64)))
        p1=Portfolio((self._b("a",2,3,1),),(Fraction(1),)); p2=Portfolio((self._b("b",1,4,2),),(Fraction(1),)); self.assertIn(p1,frontier((p1,p2)))
