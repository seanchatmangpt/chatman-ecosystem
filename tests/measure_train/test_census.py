import unittest
from scripts.measure_train.census import census
from scripts.measure_train.evidence import *
from scripts.measure_train.identity import *
class CensusCourt(unittest.TestCase):
    s=Subject('o/r','a'*40)
    def r(self,i,o): return Evidence(i,self.s,EvidenceKind.CI,'2026-08-22T05:00:00Z',o)
    def test_empty_unknown(self): self.assertEqual(census(()).standing,Standing.UNKNOWN)
    def test_failure_dominates(self): self.assertEqual(census((self.r('a',Outcome.PASS),self.r('b',Outcome.FAIL))).standing,Standing.BUILD_BROKEN)
    def test_all_green_bounded(self): self.assertEqual(census((self.r('a',Outcome.PASS),)).standing,Standing.PARTIAL_ALIVE)
if __name__=='__main__': unittest.main()
