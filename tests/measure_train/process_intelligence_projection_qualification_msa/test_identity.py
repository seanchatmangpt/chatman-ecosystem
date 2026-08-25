import unittest
from scripts.measure_train.process_intelligence_projection_qualification_msa.subject import Subject
from scripts.measure_train.process_intelligence_projection_qualification_msa.refusal import Refused
class T(unittest.TestCase):
    def test_exact_subject(self):
        self.assertEqual(Subject('o/r','a'*40,'b'*64,1).generation,1)
        with self.assertRaises(Refused): Subject('o/r','bad','b'*64)
