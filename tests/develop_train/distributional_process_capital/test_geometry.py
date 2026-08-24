import unittest
from fractions import Fraction
from scripts.develop_train.distributional_process_capital.distribution import Distribution
from scripts.develop_train.distributional_process_capital.geometry import total_variation,overlap,chi_square
from scripts.develop_train.distributional_process_capital.wasserstein import wasserstein1
class GeometryCourt(unittest.TestCase):
    def test_distinct_geometries(self):
        p=Distribution.from_mapping({"a":3,"b":1}); q=Distribution.from_mapping({"a":1,"b":3})
        self.assertEqual(total_variation(p,q),Fraction(1,2))
        self.assertEqual(overlap(p,q),Fraction(1,2))
        self.assertEqual(total_variation(p,q)+overlap(p,q),1)
        self.assertEqual(wasserstein1(p,q,{("a","b"):2}),1)
        self.assertGreater(chi_square(q,p),0)
if __name__=="__main__": unittest.main()
