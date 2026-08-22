import unittest
from datetime import datetime, timezone
from scripts.measure_train.supersession.subject import Subject
from scripts.measure_train.supersession.epoch import Epoch
from scripts.measure_train.supersession.evidence import Evidence
from scripts.measure_train.supersession.contradiction import contradictions

class TestContradiction(unittest.TestCase):
    def test_same_epoch_disagreement_is_visible(self):
        s=Subject("o/r","a"*40); e=Epoch(datetime.now(timezone.utc),1)
        rows=[Evidence(s,e,"CI","repo","a","PASS"),Evidence(s,e,"CI","repo","b","FAIL")]
        self.assertEqual(len(contradictions(rows)),1)
