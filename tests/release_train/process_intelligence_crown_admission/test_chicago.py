import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import unittest
from scripts.release_train.process_intelligence_crown_admission import *
D="e"*64; S=Subject("seanchatmangpt/chatman-ecosystem","4"*40,D)
class TestChicago(unittest.TestCase):
    def test_full_synthetic_release_path_zero_ambient_do(self):
        cov=MethodologyCoverage(frozenset(Methodology))
        rails=tuple(RailEvidence(S,r,r.value.lower(),Outcome.PASS,D) for r in Rail)
        q=qualify(S,cov,REQUIRED_OBLIGATIONS,rails=rails)
        self.assertEqual(Standing.PARTIAL_ALIVE,q.standing)
        record=machine_record(q)
        self.assertFalse(record["actuation_performed"])
        a=ReceiptNode("semantic",S,(),"1"*64,False)
        b=ReceiptNode("powl",S,(a.digest,),"2"*64,False)
        c=ReceiptNode("reactor",S,(b.digest,),"3"*64,False)
        d=ReceiptNode("distributed",S,(c.digest,),"4"*64,False)
        self.assertEqual("REPLAY_MATCH",replay([a,b,c,d],d.digest))
    def test_crown_mode_only_after_all_obligations(self):
        cov=MethodologyCoverage(frozenset(Methodology))
        q=qualify(S,cov,REQUIRED_OBLIGATIONS,crown_mode=True)
        self.assertEqual(Standing.ALIVE,q.standing)
if __name__=="__main__": unittest.main()
