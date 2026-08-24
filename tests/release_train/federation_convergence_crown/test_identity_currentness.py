import unittest
from scripts.release_train.federation_convergence_crown.api import Subject,Calibration,current_frontier,Refused

class IdentityCurrentnessCourt(unittest.TestCase):
    def test_exact_subject_and_current_frontier(self):
        s=Subject("seanchatmangpt/chatman-ecosystem","a"*40,"semantic-1",7)
        self.assertIn("@"+"a"*40,s.key)
        c=current_frontier([Calibration(6,"old",10,5),Calibration(7,"new",20,1)])
        self.assertEqual(c.digest,"new")
    def test_split_current_refuses(self):
        with self.assertRaises(Refused):
            current_frontier([Calibration(7,"a",20,1),Calibration(7,"b",20,1)])

if __name__=="__main__": unittest.main()
