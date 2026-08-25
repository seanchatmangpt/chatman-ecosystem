import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_transition_msa.subject import Subject,SubjectEpoch
from scripts.measure_train.process_intelligence_transition_msa.obligation import Obligation
from scripts.measure_train.process_intelligence_transition_msa.evidence import ObligationEvidence
from scripts.measure_train.process_intelligence_transition_msa.census import evidence_census
from scripts.measure_train.process_intelligence_transition_msa.discharge import discharge

class T(unittest.TestCase):
    def test_new_pass_discharges(self):
        now=datetime.now(timezone.utc)
        o=[Obligation("reactor","REACTOR")]
        a=SubjectEpoch(Subject("o/r","a"*40),1)
        b=SubjectEpoch(Subject("o/r","b"*40),2)
        before=evidence_census(o,[ObligationEvidence(a,"reactor","old","FAIL",now)])
        after_e=[ObligationEvidence(b,"reactor","new","PASS",now)]
        after=evidence_census(o,after_e)
        self.assertEqual(discharge(before,after,after_e)[0].obligation_id,"reactor")
