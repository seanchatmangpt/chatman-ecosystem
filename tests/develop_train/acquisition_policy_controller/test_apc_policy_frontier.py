from scripts.develop_train.acquisition_policy_controller.subject import Refusal
from scripts.develop_train.acquisition_policy_controller.policy import Policy
from scripts.develop_train.acquisition_policy_controller.frontier import PolicyFrontier,admit_frontier
import unittest
class T(unittest.TestCase):
    def test_generation_currentness(self):
        pol=Policy(1,.2,1,10,100,.5); f=PolicyFrontier(1,pol.digest,"b"*64)
        self.assertEqual(admit_frontier(f,pol,1),f)
        with self.assertRaises(Refusal): admit_frontier(f,pol,2)
