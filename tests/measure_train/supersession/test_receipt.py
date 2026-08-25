import unittest
from datetime import datetime, timezone
from scripts.measure_train.supersession.subject import Subject
from scripts.measure_train.supersession.epoch import Epoch
from scripts.measure_train.supersession.evidence import Evidence
from scripts.measure_train.supersession.receipt import manufacture_receipt

class TestReceipt(unittest.TestCase):
    def test_receipt_is_deterministic_and_non_actuating(self):
        s=Subject("o/r","a"*40); row=Evidence(s,Epoch(datetime.now(timezone.utc),1),"CI","repo","r","PASS")
        a=manufacture_receipt(s,[row],[],"PARTIAL_ALIVE")
        b=manufacture_receipt(s,[row],[],"PARTIAL_ALIVE")
        self.assertEqual(a,b)
        self.assertFalse(a["body"]["actuation_performed"])
