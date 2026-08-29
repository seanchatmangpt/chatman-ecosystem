import unittest
from scripts.release_train.promotion_admission.evidence import Axis,Outcome
from scripts.release_train.promotion_admission.compatibility import *
class T(unittest.TestCase):
    def test_states(self):
        self.assertEqual(compare_vectors({Axis.FOCUSED:Outcome.PASS},{Axis.REPOSITORY:Outcome.PASS}).state,Compatibility.UNKNOWN)
        self.assertEqual(compare_vectors({Axis.FOCUSED:Outcome.PASS},{Axis.FOCUSED:Outcome.PASS}).state,Compatibility.COMPATIBLE)
        self.assertEqual(compare_vectors({Axis.FOCUSED:Outcome.PASS},{Axis.FOCUSED:Outcome.FAIL}).state,Compatibility.DIVERGED)
if __name__=="__main__": unittest.main()
