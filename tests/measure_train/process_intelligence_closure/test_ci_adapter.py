import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_closure.subject import Subject
from scripts.measure_train.process_intelligence_closure.ci_adapter import workflow_observation

class T(unittest.TestCase):
    def test_failure_and_pending_are_not_green(self):
        s=Subject("o/r","a"*40); now=datetime.now(timezone.utc); d="1"*64
        failed=workflow_observation(s,"DISTRIBUTED","github-actions",d,{"id":32624821414,"status":"completed","conclusion":"failure"},now)
        pending=workflow_observation(s,"REPLAY","github-actions",d,{"id":2,"status":"in_progress","conclusion":None},now)
        self.assertEqual(failed.outcome,"FAIL")
        self.assertEqual(pending.outcome,"PENDING")
