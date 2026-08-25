import unittest
from scripts.measure_train.process_intelligence_transition_msa.subject import Subject,SubjectEpoch,Refused

class T(unittest.TestCase):
    def test_exact_generation(self):
        e=SubjectEpoch(Subject("o/r","a"*40),3)
        self.assertEqual(e.generation,3)
        with self.assertRaises(Refused):
            Subject("o/r","abc")
