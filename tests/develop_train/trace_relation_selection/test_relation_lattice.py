import unittest
from scripts.develop_train.trace_relation_selection import Relation, stronger_than, maximal

class TestRelationLattice(unittest.TestCase):
    def test_noncollapse(self):
        self.assertTrue(stronger_than(Relation.EXACT, Relation.STUTTER))
        self.assertTrue(stronger_than(Relation.EXACT, Relation.PARTIAL_ORDER))
        self.assertFalse(stronger_than(Relation.STUTTER, Relation.PARTIAL_ORDER))
        self.assertFalse(stronger_than(Relation.PARTIAL_ORDER, Relation.STUTTER))
        self.assertEqual(set(maximal([Relation.STUTTER, Relation.PARTIAL_ORDER, Relation.ACTIVITY])),
                         {Relation.STUTTER, Relation.PARTIAL_ORDER})
