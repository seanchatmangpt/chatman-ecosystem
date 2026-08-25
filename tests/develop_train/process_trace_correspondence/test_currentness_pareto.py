import unittest
from scripts.develop_train.process_trace_correspondence import *
from scripts.develop_train.process_trace_correspondence.currentness import require_current
from scripts.develop_train.process_trace_correspondence.pareto import Candidate,frontier
class T(unittest.TestCase):
 def test_currentness(self):
  self.assertEqual(require_current([Currentness(2,0,10),Currentness(2,1,9)],5),2)
  with self.assertRaises(Refused): require_current([Currentness(1,0,10),Currentness(2,0,10)],5)
 def test_pareto(self):
  a=Candidate("a",4,1,1,0,1); b=Candidate("b",3,.5,.5,1,2); self.assertEqual(frontier([a,b]),(a,))
