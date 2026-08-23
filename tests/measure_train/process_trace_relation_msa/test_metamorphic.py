import unittest
from scripts.measure_train.process_trace_relation_msa.relation import Relation
from scripts.measure_train.process_trace_relation_msa.metamorphic import require_stutter_law,require_commutation_law
from scripts.measure_train.process_trace_relation_msa.subject import Refused
class T(unittest.TestCase):
 def test_stutter_and_commutation(self):
  self.assertTrue(require_stutter_law(("a","b"),("a","a","b"),Relation.STUTTER))
  self.assertTrue(require_commutation_law(("a","b"),("b","a"),{("a","b")},Relation.PARTIAL_ORDER))
  with self.assertRaises(Refused): require_commutation_law(("a","b"),("b","a"),set(),Relation.PARTIAL_ORDER)
