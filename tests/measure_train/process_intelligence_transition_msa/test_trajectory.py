import unittest
from scripts.measure_train.process_intelligence_transition_msa.subject import Subject,SubjectEpoch,Refused
from scripts.measure_train.process_intelligence_transition_msa.transition import SubjectTransition
from scripts.measure_train.process_intelligence_transition_msa.trajectory import admit_trajectory

class T(unittest.TestCase):
    def test_torn_refuses(self):
        a=SubjectEpoch(Subject("o/r","a"*40),1)
        b=SubjectEpoch(Subject("o/r","b"*40),2)
        c=SubjectEpoch(Subject("o/r","c"*40),3)
        d=SubjectEpoch(Subject("o/r","d"*40),4)
        with self.assertRaises(Refused):
            admit_trajectory([SubjectTransition(a,b,"1"),SubjectTransition(c,d,"2")])
