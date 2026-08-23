import unittest
from scripts.develop_train.outcome_transport_invariance import *

S = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a" * 40 + "#" + "b" * 64)
SRC = Population.make("source", {"a": .5, "b": .3, "c": .2})
TGT = Population.make("target", {"a": .4, "b": .35, "c": .25})
CAL = Calibration(4, "c" * 64, 20, .05)

class Chicago(unittest.TestCase):
    def test_full_method_transport_invariance_and_failure_dominance(self):
        losses = {"a": .1, "b": .2, "c": .3}
        qualified = qualify(S, SRC, TGT, losses, [CAL], Cusum(threshold=1), REQUIRED)
        self.assertEqual(qualified.standing, "PARTIAL_ALIVE")
        self.assertEqual(replay(qualified.receipt, qualified.receipt.digest), "REPLAY_MATCH")

        broken = qualify(S, SRC, TGT, losses, [CAL], Cusum(threshold=1), REQUIRED, dependencies=("BUILD_BROKEN",))
        self.assertEqual(broken.standing, "BUILD_BROKEN")
        self.assertIsNone(broken.receipt)

        far = Population.make("far", {"a": .8, "b": .1, "c": .1})
        unsupported = qualify(S, SRC, far, losses, [CAL], Cusum(threshold=1), REQUIRED, max_shift=.1)
        self.assertEqual(unsupported.standing, "UNSUPPORTED")
