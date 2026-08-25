import unittest
from fractions import Fraction
from scripts.measure_train.federation_convergence_kinetics_msa.dependency import graph, propagated
from scripts.measure_train.federation_convergence_kinetics_msa.standing import standing

class TestDependencyStanding(unittest.TestCase):
    def test_red_parent_blocks_green_consumer(self):
        adjacency = graph(["up", "down"], [("down", "up")])
        self.assertEqual(propagated({"up": "BUILD_BROKEN", "down": "PARTIAL_ALIVE"}, adjacency)["down"], "BUILD_BROKEN")
        self.assertEqual(standing("CAPABLE", "CALIBRATED", 20, Fraction(0), ["BUILD_BROKEN"]), "BUILD_BROKEN")
