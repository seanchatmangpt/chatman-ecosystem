import unittest
from datetime import datetime, timezone
from scripts.measure_train.selection_provenance.subject import Subject
from scripts.measure_train.selection_provenance.strategy import StrategyBinding
from scripts.measure_train.selection_provenance.selection import SelectionEvidence
from scripts.measure_train.selection_provenance.frontier import SelectionFrontier
from scripts.measure_train.selection_provenance.drift import classify_drift

class TestDrift(unittest.TestCase):
    def test_policy_and_candidate_frontier_drift_are_distinct(self):
        s=Subject("o/r","a"*40); cut="2"*64
        old=StrategyBinding("LATEST_COMPLETE","1"*64)
        sel=SelectionEvidence(s,old,(cut,),cut,"3"*64,datetime.now(timezone.utc),"x")
        self.assertEqual(classify_drift(sel,SelectionFrontier(StrategyBinding("LATEST_COMPLETE","4"*64),(cut,),cut)),"POLICY_DRIFT")
        self.assertEqual(classify_drift(sel,SelectionFrontier(old,(cut,"5"*64),cut)),"CANDIDATE_FRONTIER_DRIFT")
