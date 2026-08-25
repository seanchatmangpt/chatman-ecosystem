import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import unittest
from scripts.release_train.process_intelligence_crown_admission import *
D="a"*64; S=Subject("o/r","2"*40,D)
class TestAuthorityReceipts(unittest.TestCase):
    def test_direct_do_requires_brce_receipt_postcondition(self):
        with self.assertRaises(Refused): admit_authority(AuthorityEvidence(ActionClass.DO,None,None,False))
        admit_authority(AuthorityEvidence(ActionClass.DO,"BRCE","b"*64,True))
    def test_receipt_dag_replay(self):
        a=ReceiptNode("semantic",S,(),"c"*64,False)
        b=ReceiptNode("runtime",S,(a.digest,),"d"*64,False)
        self.assertEqual("REPLAY_MATCH",replay([a,b],b.digest))
    def test_ambient_actuation_refuses(self):
        with self.assertRaises(Refused): admit_authority(AuthorityEvidence(ActionClass.CONSTRUCT,None,None,True))
if __name__=="__main__": unittest.main()
