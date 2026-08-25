import unittest
from scripts.develop_train.process_trace_correspondence import *
from scripts.develop_train.process_trace_correspondence.conformance import score
class T(unittest.TestCase):
 def test_bounded(self):
  s=Subject("o/r@"+"d"*40); a=Trace(s,"a",(Event("A","1"),)); self.assertTrue(witness(a,a,Relation.EXACT,2).matched)
  with self.assertRaises(Refused): witness(a,a,Relation.EXACT,1)
 def test_directional(self):
  s=Subject("o/r@"+"e"*40); r=Trace(s,"r",(Event("A","1"),Event("B","1"))); o=Trace(s,"o",(Event("A","1"),)); c=score(r,o); self.assertEqual(c.precision,1.0); self.assertEqual(c.recall,0.5)
