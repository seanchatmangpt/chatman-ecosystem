import unittest
from scripts.measure_train.process_intelligence_transition_msa.obligation import Obligation
from scripts.measure_train.process_intelligence_transition_msa.subject import Refused

class T(unittest.TestCase):
    def test_kind(self):
        self.assertEqual(Obligation("reactor","REACTOR").kind,"REACTOR")
        with self.assertRaises(Refused):
            Obligation("x","MAGIC")
