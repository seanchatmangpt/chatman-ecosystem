import unittest
from scripts.develop_train.outcome_transport_invariance import *

SRC = Population.make("source", {"a": .5, "b": .3, "c": .2})
TGT = Population.make("target", {"a": .4, "b": .35, "c": .25})
CAL = Calibration(4, "c" * 64, 20, .05)

class StressCurrentness(unittest.TestCase):
    def test_stress_and_currentness(self):
        self.assertLess(erosion(SRC, TGT, "c", .5).overlap, 1)
        self.assertGreaterEqual(shift(SRC, TGT, "a", .1).shift, 0)
        detector = Cusum(threshold=.5)
        for _ in range(3):
            detector = detector.update(.2)
        self.assertTrue(detector.changed)

    def test_split_current_refuses(self):
        with self.assertRaises(Refused):
            current([CAL, Calibration(4, "d" * 64, 20, .05)])
