import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import unittest
from scripts.release_train.process_intelligence_crown_admission import Subject, Methodology, MethodologyCoverage, Refused

D="a"*64
class TestIdentityMethodology(unittest.TestCase):
    def test_exact_subject_and_complete_methods(self):
        s=Subject("seanchatmangpt/chatman-ecosystem","1"*40,D)
        self.assertIn("@",s.canonical)
        self.assertTrue(MethodologyCoverage(frozenset(Methodology)).complete)
    def test_short_sha_refuses(self):
        with self.assertRaises(Refused): Subject("o/r","abc",D)
if __name__=="__main__": unittest.main()
