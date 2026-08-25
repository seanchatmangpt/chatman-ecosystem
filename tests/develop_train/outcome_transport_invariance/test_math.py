import unittest
from scripts.develop_train.outcome_transport_invariance import *

S = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a" * 40 + "#" + "b" * 64)
SRC = Population.make("source", {"a": .5, "b": .3, "c": .2})
TGT = Population.make("target", {"a": .4, "b": .35, "c": .25})

class TransportMath(unittest.TestCase):
    def test_geometry_weights_and_estimators(self):
        self.assertAlmostEqual(tv(SRC, TGT), .1)
        self.assertGreater(hellinger(SRC, TGT), 0)
        self.assertGreater(js(SRC, TGT), 0)
        weights = require_ess(importance_weights(SRC, TGT), 2)
        self.assertGreater(weights.ess, 2)
        losses = {"a": .1, "b": .2, "c": .4}
        self.assertNotEqual(ht(losses, weights), sn(losses, weights))

    def test_positivity_refuses(self):
        with self.assertRaises(Refused):
            require_positivity(SRC, Population.make("bad", {"a": .5, "d": .5}))
