import unittest
from scripts.measure_train.validation_independence_realization_msa.subject import Subject,Refused
from scripts.measure_train.validation_independence_realization_msa.graph import Evidence,admit_graph,ancestors
class T(unittest.TestCase):
 def test_exact_and_acyclic(self):
  s=Subject("o/r","a"*40,"b"*64); self.assertEqual(s.repo,"o/r")
  g=admit_graph([Evidence("r",(),0,"c"*64),Evidence("x",("r",),1,"d"*64)])
  self.assertEqual(ancestors(g,"x"),frozenset({"r"}))
  with self.assertRaises(Refused): admit_graph([Evidence("a",("b",),1,"a"*64),Evidence("b",("a",),1,"b"*64)])
