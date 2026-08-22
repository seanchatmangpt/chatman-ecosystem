import unittest
from scripts.develop_train.regime_ensemble.budget import EvidenceBudget
class TestBudget(unittest.TestCase):
    def test_each_resource_axis_fails_closed(self):
        b=EvidenceBudget(5,3,2.0)
        for args, token in [((6,3,1.0),"SAMPLE"),((5,4,1.0),"DETECTOR"),((5,3,3.0),"SCORE")]:
            with self.assertRaisesRegex(ValueError,token): b.admit(*args)
if __name__ == "__main__": unittest.main()
