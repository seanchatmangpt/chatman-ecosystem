import unittest
from fractions import Fraction
from scripts.measure_train.trace_relation_selector_realization_msa.relation import Relation
from scripts.measure_train.trace_relation_selector_realization_msa.pareto_regret import OutcomeVector,frontier
from scripts.measure_train.trace_relation_selector_realization_msa.stability import jaccard
class T(unittest.TestCase):
 def test_partial_order_and_stutter_both_survive_when_incomparable(self):
  rows=[OutcomeVector(Relation.STUTTER,100000,10),OutcomeVector(Relation.PARTIAL_ORDER,100000,10)]
  self.assertEqual({x.relation for x in frontier(rows)},{Relation.STUTTER,Relation.PARTIAL_ORDER})
  self.assertEqual(jaccard([1],[1]),Fraction(1))
