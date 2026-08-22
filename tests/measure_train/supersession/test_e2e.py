import unittest
from datetime import datetime, timezone, timedelta
from scripts.measure_train.supersession.subject import Subject
from scripts.measure_train.supersession.epoch import Epoch
from scripts.measure_train.supersession.evidence import Evidence
from scripts.measure_train.supersession.relation import Supersession
from scripts.measure_train.supersession.qualify import qualify
from scripts.measure_train.supersession.replay import replay

class TestE2E(unittest.TestCase):
    def test_stale_green_cannot_represent_new_failure(self):
        s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
        old=Evidence(s,Epoch(now,1),"CI","repository","run-old","PASS")
        new=Evidence(s,Epoch(now+timedelta(seconds=1),2),"CI","repository","run-new","FAIL")
        q=qualify(s,[old,new],[Supersession("run-new","run-old","NEW_RUN")])
        self.assertEqual(q["standing"],"BUILD_BROKEN")
        self.assertEqual(q["historical"][0].outcome,"PASS")
        self.assertFalse(q["actuation_performed"])
        self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
