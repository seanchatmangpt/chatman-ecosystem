import unittest
from fractions import Fraction
from scripts.develop_train.distributional_process_capital.errors import Refused
from scripts.develop_train.distributional_process_capital.calibration import Calibration,current
from scripts.develop_train.distributional_process_capital.pareto import Candidate,frontier
from scripts.develop_train.distributional_process_capital.selectors import Strategy,select
class CalibrationSelectionCourt(unittest.TestCase):
    def test_current_and_noncollapsed_selection(self):
        c=Calibration(2,"c"*64,10,1,Fraction(1,10)); self.assertTrue(c.admitted()); self.assertEqual(current([c]),c)
        candidates=(Candidate("a",Fraction(1,10),Fraction(2,10),Fraction(1,10),5),Candidate("b",Fraction(2,10),Fraction(15,100),Fraction(2,10),8))
        self.assertNotEqual(select(candidates,Strategy.MIN_NOMINAL),select(candidates,Strategy.MIN_WORST))
        self.assertEqual(len(frontier(candidates)),2)
    def test_split_current_refuses(self):
        with self.assertRaises(Refused): current([Calibration(3,"a"*64,10,0,Fraction(1,10)),Calibration(3,"b"*64,10,0,Fraction(1,10))])
if __name__=="__main__": unittest.main()
