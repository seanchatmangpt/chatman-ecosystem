import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_transition_msa.subject import Subject,SubjectEpoch,Refused
from scripts.measure_train.process_intelligence_transition_msa.workflow_adapter import WorkflowObservation,workflow_to_evidence

class T(unittest.TestCase):
    def test_failure_and_foreign(self):
        now=datetime.now(timezone.utc)
        e=SubjectEpoch(Subject("o/r","a"*40),1)
        row=WorkflowObservation("1","a"*40,"ci","completed","failure",now)
        self.assertEqual(workflow_to_evidence(e,"ci",row).state,"FAIL")
        bad=WorkflowObservation("2","b"*40,"ci","completed","success",now)
        with self.assertRaises(Refused):
            workflow_to_evidence(e,"ci",bad)
