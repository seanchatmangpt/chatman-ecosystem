import unittest
from scripts.develop_train.epoch_discharge.frontier import ConsumerState
from scripts.develop_train.epoch_discharge.strategy import CompletionStrategy,complete
class T(unittest.TestCase):
 def test_strategies_do_not_collapse(self):
  s=(ConsumerState("a","REQUALIFIED","REQUALIFIED"),ConsumerState("b","PENDING_ACK",None),ConsumerState("c","REQUALIFIED","REQUALIFIED"))
  self.assertFalse(complete(s,CompletionStrategy.ALL)); self.assertTrue(complete(s,CompletionStrategy.QUORUM)); self.assertTrue(complete(s,CompletionStrategy.CRITICAL_PATH,frozenset({"a"})))
