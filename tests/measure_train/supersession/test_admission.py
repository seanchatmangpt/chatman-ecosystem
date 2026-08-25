import unittest
from datetime import datetime, timezone
from scripts.measure_train.supersession.subject import Subject, Refused
from scripts.measure_train.supersession.epoch import Epoch
from scripts.measure_train.supersession.evidence import Evidence
from scripts.measure_train.supersession.admission import admit

class TestAdmission(unittest.TestCase):
    def test_foreign_subject_refuses(self):
        a, b = Subject("o/r","a"*40), Subject("o/r","b"*40)
        item = Evidence(b, Epoch(datetime.now(timezone.utc),1), "CI","repo","run1","PASS")
        with self.assertRaises(Refused):
            admit(a,[item])
