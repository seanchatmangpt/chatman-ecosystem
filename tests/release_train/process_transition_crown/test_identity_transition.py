import unittest
from scripts.release_train.process_transition_crown import SubjectEpoch, SubjectTransition
from scripts.release_train.process_transition_crown.refusal import Refused

class IdentityTransitionTest(unittest.TestCase):
    def test_exact_and_contiguous(self):
        a=SubjectEpoch("seanchatmangpt/chatman-ecosystem","a"*40,0,"sem")
        b=a.advance("b"*40,"sem2")
        self.assertEqual(SubjectTransition(a,b).after.generation,1)
    def test_short_sha_refuses(self):
        with self.assertRaises(Refused): SubjectEpoch("x/y","abc",0,"sem")
    def test_torn_generation_refuses(self):
        a=SubjectEpoch("x/y","a"*40,0,"s")
        b=SubjectEpoch("x/y","b"*40,2,"t")
        with self.assertRaises(Refused): SubjectTransition(a,b)

if __name__=="__main__": unittest.main()
