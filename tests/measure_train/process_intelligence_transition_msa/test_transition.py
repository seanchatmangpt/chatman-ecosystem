import unittest
from scripts.measure_train.process_intelligence_transition_msa.subject import Subject,SubjectEpoch,Refused
from scripts.measure_train.process_intelligence_transition_msa.transition import SubjectTransition

class T(unittest.TestCase):
    def test_contiguous(self):
        a=SubjectEpoch(Subject("o/r","a"*40),1)
        b=SubjectEpoch(Subject("o/r","b"*40),2)
        self.assertEqual(SubjectTransition(a,b,"t").after,b)
        with self.assertRaises(Refused):
            SubjectTransition(a,SubjectEpoch(Subject("o/r","c"*40),3),"x")
