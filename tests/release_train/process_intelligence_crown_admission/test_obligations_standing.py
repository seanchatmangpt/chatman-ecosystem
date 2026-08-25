import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import unittest
from scripts.release_train.process_intelligence_crown_admission import *
D="d"*64; S=Subject("o/r","3"*40,D)
class TestObligationsStanding(unittest.TestCase):
    def test_missing_exact_obligation_is_unknown(self):
        cov=MethodologyCoverage(frozenset(Methodology))
        q=qualify(S,cov,frozenset({Obligation.POWL_SOUNDNESS}))
        self.assertEqual(Standing.UNKNOWN,q.standing)
        self.assertIn("EXACT_HEAD",q.census.missing)
    def test_failure_dominates(self):
        cov=MethodologyCoverage(frozenset(Methodology))
        q=qualify(S,cov,REQUIRED_OBLIGATIONS,{Obligation.MULTI_REGION_TLS})
        self.assertEqual(Standing.BUILD_BROKEN,q.standing)
    def test_complete_scoped_gate_caps_partial_alive(self):
        cov=MethodologyCoverage(frozenset(Methodology))
        q=qualify(S,cov,REQUIRED_OBLIGATIONS)
        self.assertEqual(Standing.PARTIAL_ALIVE,q.standing)
if __name__=="__main__": unittest.main()
