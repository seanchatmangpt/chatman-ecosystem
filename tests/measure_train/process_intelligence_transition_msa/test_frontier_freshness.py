import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.process_intelligence_transition_msa.subject import Subject,SubjectEpoch
from scripts.measure_train.process_intelligence_transition_msa.evidence import ObligationEvidence
from scripts.measure_train.process_intelligence_transition_msa.frontier import current_subject_frontier
from scripts.measure_train.process_intelligence_transition_msa.freshness import freshness

class T(unittest.TestCase):
    def test_latest_and_stale(self):
        now=datetime.now(timezone.utc)
        a=SubjectEpoch(Subject("o/r","a"*40),1)
        b=SubjectEpoch(Subject("o/r","b"*40),2)
        self.assertEqual(current_subject_frontier([a,b])[0],b)
        e=ObligationEvidence(b,"ci","x","PASS",now-timedelta(seconds=10))
        self.assertEqual(freshness(e,now,5),"STALE")
