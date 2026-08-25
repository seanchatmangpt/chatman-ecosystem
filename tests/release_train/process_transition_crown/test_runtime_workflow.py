import unittest
from scripts.release_train.process_transition_crown import SubjectEpoch, RuntimeReceipt, WorkflowResult, State
from scripts.release_train.process_transition_crown.refusal import Refused

class RuntimeWorkflowTest(unittest.TestCase):
    def setUp(self): self.s=SubjectEpoch("x/y","a"*40,1,"sem")
    def test_tls_contradiction_refuses(self):
        r=RuntimeReceipt(self.s,"two-region inet_tls","inet_tcp",False,"",0)
        with self.assertRaises(Refused): r.admit(self.s)
    def test_pending_stays_unknown(self):
        self.assertEqual(WorkflowResult(self.s.sha,"ci","in_progress").state_for(self.s),State.UNKNOWN)
    def test_foreign_head_refuses(self):
        with self.assertRaises(Refused): WorkflowResult("b"*40,"ci","success").state_for(self.s)

if __name__=="__main__": unittest.main()
