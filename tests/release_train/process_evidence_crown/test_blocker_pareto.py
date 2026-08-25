import unittest
from fractions import Fraction
from scripts.release_train.process_evidence_crown import *
class T(unittest.TestCase):
 def test_minimal_cuts(self):
  req={'crown':{'tls','engine'},'global':{'tls','oracle'}}
  self.assertEqual(minimal_blocker_cutsets(req,{'tls','engine','oracle'}),(('tls',),))
 def test_pareto_preserves_incomparability(self):
  a=Candidate('a',Fraction(1,10),Fraction(1,5),Fraction(5),Fraction(1,2)); b=Candidate('b',Fraction(1,5),Fraction(1,10),Fraction(1),Fraction(1,3)); c=Candidate('c',Fraction(1,2),Fraction(1,2),Fraction(10),Fraction(0))
  self.assertEqual({x.id for x in frontier([a,b,c])},{'a','b'})
