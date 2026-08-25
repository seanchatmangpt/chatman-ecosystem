import unittest
from scripts.develop_train.process_trace_correspondence import *
from scripts.develop_train.process_trace_correspondence.relation import equivalent,discharges
from scripts.develop_train.process_trace_correspondence.partial_order import equivalent as po
class T(unittest.TestCase):
 def test_noncollapse(self):
  s=Subject("o/r@"+"b"*40); a=Trace(s,"a",(Event("A","1"),Event("A","1"),Event("B","1"))); b=Trace(s,"b",(Event("A","1"),Event("B","1")))
  self.assertFalse(equivalent(a,b,Relation.ACTIVITY)); self.assertTrue(equivalent(a,b,Relation.STUTTER)); self.assertTrue(discharges(Relation.EXACT,Relation.STUTTER)); self.assertFalse(discharges(Relation.STUTTER,Relation.EXACT))
 def test_partial_order(self):
  s=Subject("o/r@"+"c"*40); a=Trace(s,"a",(Event("A","1"),Event("B","1"))); b=Trace(s,"b",(Event("B","1"),Event("A","1"))); ind=Independence.from_pairs([("A","B")]); self.assertTrue(po(a,b,ind))
