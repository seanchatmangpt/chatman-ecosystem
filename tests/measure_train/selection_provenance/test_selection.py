import unittest
from datetime import datetime, timezone
from scripts.measure_train.selection_provenance.subject import Subject, Refused
from scripts.measure_train.selection_provenance.strategy import StrategyBinding
from scripts.measure_train.selection_provenance.selection import SelectionEvidence

class TestSelection(unittest.TestCase):
    def test_selected_cut_must_belong_to_candidate_set(self):
        s = Subject("o/r","a"*40)
        st = StrategyBinding("LATEST_COMPLETE","1"*64)
        with self.assertRaises(Refused):
            SelectionEvidence(s, st, ("2"*64,), "3"*64, "4"*64, datetime.now(timezone.utc), "selector")
