import unittest
from datetime import datetime, timezone
from scripts.measure_train.supersession.subject import Subject
from scripts.measure_train.supersession.epoch import Epoch
from scripts.measure_train.supersession.evidence import Evidence
from scripts.measure_train.supersession.standing import standing

class TestStanding(unittest.TestCase):
    def test_green_never_crowns_alive(self):
        s=Subject("o/r","a"*40)
        row=Evidence(s,Epoch(datetime.now(timezone.utc),1),"CI","repo","run","PASS")
        self.assertEqual(standing([row]),"PARTIAL_ALIVE")
