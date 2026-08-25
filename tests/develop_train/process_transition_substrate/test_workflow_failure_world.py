import unittest
from scripts.develop_train.process_transition_substrate import *
class T(unittest.TestCase):
 def test_workflow(self):
  sha="1"*40
  self.assertEqual(adapt(WorkflowResult(sha,"success"),sha),State.PASS)
  self.assertEqual(adapt(WorkflowResult(sha,None),sha),State.UNKNOWN)
 def test_failure_world(self):
  FailureWorld(frozenset({"node_down","partition","latency","loss","version_skew","certificate","ambiguous_do"})).require_complete()
