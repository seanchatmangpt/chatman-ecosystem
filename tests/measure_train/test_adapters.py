import unittest
from scripts.measure_train.adapters import *
from scripts.measure_train.identity import *
from scripts.measure_train.evidence import Outcome
class AdapterCourt(unittest.TestCase):
    def setUp(self): self.s=Subject('o/r','a'*40)
    def test_ci_foreign_head_refuses(self):
        with self.assertRaises(Refused): github_ci(self.s,[{'id':1,'head_sha':'b'*40,'updated_at':'2026-08-22T05:00:00Z','status':'success'}])
    def test_pending_preserved(self): self.assertEqual(github_ci(self.s,[{'id':1,'head_sha':'a'*40,'updated_at':'2026-08-22T05:00:00Z','status':'queued'}])[0].outcome,Outcome.PENDING)
    def test_closed_unmerged_not_pass(self): self.assertEqual(github_pr(self.s,{'number':1,'head_sha':'a'*40,'updated_at':'2026-08-22T05:00:00Z','state':'closed','merged':False}).outcome,Outcome.UNKNOWN)
if __name__=='__main__': unittest.main()
