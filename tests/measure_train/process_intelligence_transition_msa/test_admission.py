import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_transition_msa.subject import Subject,SubjectEpoch,Refused
from scripts.measure_train.process_intelligence_transition_msa.obligation import Obligation
from scripts.measure_train.process_intelligence_transition_msa.evidence import ObligationEvidence
from scripts.measure_train.process_intelligence_transition_msa.admission import admit_evidence

class T(unittest.TestCase):
    def test_foreign_head_refuses(self):
        now=datetime.now(timezone.utc)
        a=SubjectEpoch(Subject("o/r","a"*40),1)
        b=SubjectEpoch(Subject("o/r","b"*40),2)
        row=ObligationEvidence(a,"ci","run","PASS",now)
        with self.assertRaises(Refused):
            admit_evidence(b,[Obligation("ci","CI")],[row],now)
