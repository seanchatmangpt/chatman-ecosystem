import unittest
from scripts.measure_train.evidence import *
from scripts.measure_train.identity import Subject, Standing
class EvidenceCourt(unittest.TestCase):
    def e(self,o): return Evidence("x",Subject("o/r","a"*40),EvidenceKind.CI,"2026-08-22T05:00:00Z",o)
    def test_success_ceiling(self): self.assertEqual(self.e(Outcome.PASS).standing(), Standing.PARTIAL_ALIVE)
    def test_pending_unknown(self): self.assertEqual(self.e(Outcome.PENDING).standing(), Standing.UNKNOWN)
    def test_failure_broken(self): self.assertEqual(self.e(Outcome.FAIL).standing(), Standing.BUILD_BROKEN)
    def test_unsupported_distinct(self): self.assertEqual(self.e(Outcome.UNSUPPORTED).standing(), Standing.UNSUPPORTED)
if __name__=='__main__': unittest.main()
