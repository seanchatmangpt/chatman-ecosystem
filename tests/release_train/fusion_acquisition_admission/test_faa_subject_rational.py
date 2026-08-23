import sys,unittest
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.release_train.fusion_acquisition_admission.subject import Subject
from scripts.release_train.fusion_acquisition_admission.rational import unit
from scripts.release_train.fusion_acquisition_admission.errors import Refused
class TestSubjectRational(unittest.TestCase):
    def test_exact_and_bounds(self):
        s=Subject("o/r@"+"a"*40); self.assertEqual(s.canonical(),"o/r@"+"a"*40); self.assertEqual(unit(Fraction(1,3)),Fraction(1,3))
        with self.assertRaises(Refused): Subject("o/r@abc")
        with self.assertRaises(Refused): unit(2)
