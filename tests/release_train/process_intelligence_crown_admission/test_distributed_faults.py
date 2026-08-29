import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import unittest
from datetime import datetime, timezone, timedelta
from scripts.release_train.process_intelligence_crown_admission import *
D="f"*64; S=Subject("o/r","1"*40,D); NOW=datetime(2026,8,23,8,30,tzinfo=timezone.utc)
class TestDistributedFaults(unittest.TestCase):
    def test_multi_region_tls_currentness(self):
        rows=[RegionWitness(S,"h1","us-west","erts-15","a"*64,D,NOW,10,0),RegionWitness(S,"h2","eu-west","erts-15","b"*64,D,NOW,20,1)]
        self.assertTrue(require_multi_region(rows,NOW,timedelta(minutes=5),50,10))
    def test_complete_failure_matrix(self):
        ws=[FaultWitness(f,True,None if f is Fault.AMBIGUOUS_DO else "a"*64,False) for f in Fault]
        self.assertTrue(require_fault_closure(ws))
    def test_partition_staleness_refuses(self):
        r=RegionWitness(S,"h1","r1","v","a"*64,D,NOW-timedelta(hours=1),1,0)
        r2=RegionWitness(S,"h2","r2","v","b"*64,D,NOW,1,0)
        with self.assertRaises(Refused): require_multi_region([r,r2],NOW,timedelta(minutes=5),50,10)
if __name__=="__main__": unittest.main()
