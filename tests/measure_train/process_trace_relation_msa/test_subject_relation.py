import unittest
from scripts.measure_train.process_trace_relation_msa.subject import Subject,Refused
from scripts.measure_train.process_trace_relation_msa.relation import Relation,require_noncollapsed
class T(unittest.TestCase):
 def test_exact_and_lattice(self):
  Subject("o/r","a"*40,"b"*64)
  with self.assertRaises(Refused): Subject("o/r","short","b"*64)
  self.assertTrue(require_noncollapsed({r:True for r in Relation}))
