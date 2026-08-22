import unittest
from datetime import datetime, timezone
from scripts.measure_train.selection_provenance.subject import Subject
from scripts.measure_train.selection_provenance.strategy import StrategyBinding
from scripts.measure_train.selection_provenance.selection import SelectionEvidence
from scripts.measure_train.selection_provenance.contradiction import contradictions

class TestContradiction(unittest.TestCase):
    def test_same_selector_epoch_cannot_select_two_cuts(self):
        now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); st=StrategyBinding("LATEST_COMPLETE","1"*64)
        a=SelectionEvidence(s,st,("2"*64,"3"*64),"2"*64,"4"*64,now,"sel")
        b=SelectionEvidence(s,st,("2"*64,"3"*64),"3"*64,"5"*64,now,"sel")
        self.assertEqual(len(contradictions((a,b))),1)
