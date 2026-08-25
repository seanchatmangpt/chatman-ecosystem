import unittest
from fractions import Fraction
from scripts.develop_train.trace_relation_selection import *
from scripts.develop_train.trace_relation_selection.strongest import select_strongest_defensible
from scripts.develop_train.trace_relation_selection.minimax import select_minimax
from scripts.develop_train.trace_relation_selection.information import select_information_seeking

class TestSelectorDifferential(unittest.TestCase):
    def test_selector_families_can_disagree(self):
        exact=CalibrationEvidence(Relation.EXACT,1,100,4,10,Fraction(5))
        activity=CalibrationEvidence(Relation.ACTIVITY,1,100,1,1,Fraction(1))
        self.assertEqual(select_strongest_defensible([Relation.EXACT,Relation.ACTIVITY]),(Relation.EXACT,))
        self.assertEqual(select_minimax([exact,activity]),Relation.ACTIVITY)
        self.assertIn(select_information_seeking([exact,activity]),{Relation.EXACT,Relation.ACTIVITY})
