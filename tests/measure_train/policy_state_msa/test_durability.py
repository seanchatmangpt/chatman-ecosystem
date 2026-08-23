import unittest
from scripts.measure_train.policy_state_msa.durability import RestartWitness,durability_state
class T(unittest.TestCase):
    def test_restart_preserves_state(self):
        self.assertEqual(durability_state(RestartWitness("a"*40,2,2,"2"*64,"2"*64,False,True)),"PASS")
