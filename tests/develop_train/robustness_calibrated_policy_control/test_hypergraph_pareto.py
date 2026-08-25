import unittest
from fractions import Fraction as F
from scripts.develop_train.robustness_calibrated_policy_control.identity import PolicyIdentity
from scripts.develop_train.robustness_calibrated_policy_control.hypergraph import CompatibilityHypergraph
from scripts.develop_train.robustness_calibrated_policy_control.pareto import Candidate,frontier
class T(unittest.TestCase):
 def test_maximal_feasible_and_pareto(self):
  a=PolicyIdentity(1,'a'*64); b=PolicyIdentity(1,'b'*64); c=PolicyIdentity(1,'c'*64)
  h=CompatibilityHypergraph(frozenset({frozenset((a.digest,b.digest))}))
  sets=h.maximal_feasible((a,b,c),2)
  self.assertEqual({tuple(x.digest[0] for x in s) for s in sets},{('a','c'),('b','c')})
  x=Candidate(('x',),F(3,4),F(1,4),F(3),F(1),F(1)); y=Candidate(('y',),F(1,2),F(1,2),F(2),F(2),F(2))
  self.assertEqual(frontier((x,y)),(x,))
