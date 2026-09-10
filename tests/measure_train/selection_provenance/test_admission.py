import unittest
from datetime import datetime, timezone
from scripts.measure_train.selection_provenance.subject import Subject, Refused
from scripts.measure_train.selection_provenance.strategy import StrategyBinding
from scripts.measure_train.selection_provenance.candidate import CutCandidate
from scripts.measure_train.selection_provenance.selection import SelectionEvidence
from scripts.measure_train.selection_provenance.frontier import SelectionFrontier
from scripts.measure_train.selection_provenance.admission import admit_selection

class TestAdmission(unittest.TestCase):
    def test_stale_strategy_selection_refuses(self):
        now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); cut="2"*64
        candidate=CutCandidate(cut,s,"3"*64,1,now,True)
        selection=SelectionEvidence(s,StrategyBinding("LATEST_COMPLETE","4"*64),(cut,),cut,"5"*64,now,"sel")
        frontier=SelectionFrontier(StrategyBinding("MAX_FRESHNESS","4"*64),(cut,),cut)
        with self.assertRaisesRegex(Refused,"STRATEGY_DRIFT"):
            admit_selection(selection,frontier,[candidate],now)
