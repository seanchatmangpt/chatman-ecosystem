import unittest
from scripts.measure_train.trace_relation_selector_realization_msa.subject import Subject,Refused
from scripts.measure_train.trace_relation_selector_realization_msa.relation import Relation,comparable,require_noncollapsed
from scripts.measure_train.trace_relation_selector_realization_msa.selector import Selector,SelectorIdentity
class T(unittest.TestCase):
 def test_exact_identity_and_noncollapse(self):
  s=Subject("o/r","a"*40,"b"*64); self.assertEqual(s.repo,"o/r")
  self.assertFalse(comparable(Relation.STUTTER,Relation.PARTIAL_ORDER)); self.assertTrue(require_noncollapsed())
  with self.assertRaises(Refused): Subject("o/r","bad","b"*64)
  self.assertEqual(SelectorIdentity(Selector.MINIMAX_ERROR,1,"c"*64).generation,1)
