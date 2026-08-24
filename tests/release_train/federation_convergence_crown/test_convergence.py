import unittest
from fractions import Fraction
from scripts.release_train.federation_convergence_crown.api import Epoch,admit_trajectory,fixed_point,positive_cusum

class ConvergenceCourt(unittest.TestCase):
    def test_zero_red_fixed_point_requires_dwell(self):
        epochs=[Epoch(1,"x",1,3),Epoch(2,"y",0,0),Epoch(3,"y",0,0),Epoch(4,"y",0,0)]
        self.assertTrue(fixed_point(admit_trajectory(epochs),3))
    def test_inclusive_cusum_threshold(self):
        drift,score=positive_cusum([Fraction(1,10),Fraction(2,10)],0,Fraction(3,10))
        self.assertTrue(drift)
        self.assertEqual(score,Fraction(3,10))

if __name__=="__main__": unittest.main()
