import unittest
from datetime import datetime, timezone
from scripts.measure_train.supersession.subject import Subject
from scripts.measure_train.supersession.epoch import Epoch
from scripts.measure_train.supersession.evidence import Evidence
from scripts.measure_train.supersession.telemetry import project

class TestTelemetry(unittest.TestCase):
    def test_current_and_historical_are_distinct(self):
        s=Subject("o/r","a"*40); e=Epoch(datetime.now(timezone.utc),1)
        a=Evidence(s,e,"CI","repo","a","PASS"); b=Evidence(s,e,"CI","repo","b","FAIL")
        events=project(s,[a],[b])
        self.assertEqual({x["evidence_state"] for x in events},{"CURRENT","SUPERSEDED"})
