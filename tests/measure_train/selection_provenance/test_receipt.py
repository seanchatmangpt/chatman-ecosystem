import unittest
from datetime import datetime, timezone
from scripts.measure_train.selection_provenance.subject import Subject
from scripts.measure_train.selection_provenance.strategy import StrategyBinding
from scripts.measure_train.selection_provenance.candidate import CutCandidate
from scripts.measure_train.selection_provenance.selection import SelectionEvidence
from scripts.measure_train.selection_provenance.receipt import manufacture_receipt

class TestReceipt(unittest.TestCase):
    def test_receipt_deterministic_and_non_actuating(self):
        now=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject("o/r","a"*40); cut="2"*64
        st=StrategyBinding("MIN_SKEW","1"*64,(("weight","7"),))
        c=CutCandidate(cut,s,"3"*64,4,now,True)
        sel=SelectionEvidence(s,st,(cut,),cut,"4"*64,now,"sel")
        a=manufacture_receipt(sel,c,"CURRENT","PARTIAL_ALIVE")
        b=manufacture_receipt(sel,c,"CURRENT","PARTIAL_ALIVE")
        self.assertEqual(a,b); self.assertFalse(a["body"]["actuation_performed"])
