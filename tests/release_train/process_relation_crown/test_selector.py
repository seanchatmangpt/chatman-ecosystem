import unittest
from scripts.release_train.process_relation_crown.selector import *
from scripts.release_train.process_relation_crown.relation import Relation
class T(unittest.TestCase):
 def test_strategies_noncollapse(self):
  rows=[Candidate(Relation.EXACT,.04,.10,5,.1),Candidate(Relation.ACTIVITY,.01,.01,1,.8),Candidate(Relation.PARTIAL_ORDER,.02,.04,2,.5)]
  self.assertEqual(select(rows,Strategy.STRONGEST_DEFENSIBLE).relation,Relation.EXACT)
  self.assertEqual(select(rows,Strategy.MINIMAX_ERROR).relation,Relation.ACTIVITY)
  self.assertEqual(select(rows,Strategy.INFORMATION_GAIN).relation,Relation.ACTIVITY)
  self.assertTrue(pareto(rows))
