import unittest
from scripts.develop_train.evidence_realization_control import *
class T(unittest.TestCase):
 def test_cutsets(self): self.assertEqual(minimal_blocker_cutsets({'a','b'},{'b':{'a'}}),(frozenset({'a'}),))
 def test_pareto(self):
  a=Candidate('a',.1,.1,1,1); b=Candidate('b',.2,.2,2,0); self.assertEqual(frontier([a,b]),(a,))
