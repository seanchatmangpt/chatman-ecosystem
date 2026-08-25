import unittest
from datetime import datetime, timezone, timedelta
from scripts.measure_train.supersession.subject import Subject
from scripts.measure_train.supersession.epoch import Epoch
from scripts.measure_train.supersession.evidence import Evidence
from scripts.measure_train.supersession.relation import Supersession
from scripts.measure_train.supersession.frontier import resolve_frontier

class TestFrontier(unittest.TestCase):
    def test_forward_supersession(self):
        s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
        old=Evidence(s,Epoch(now,1),"CI","repo","run1","PASS")
        new=Evidence(s,Epoch(now+timedelta(seconds=1),2),"CI","repo","run2","FAIL")
        current,historical=resolve_frontier([old,new],[Supersession("run2","run1","NEW_RUN")])
        self.assertEqual(current[0].source_id,"run2")
        self.assertEqual(historical[0].source_id,"run1")
