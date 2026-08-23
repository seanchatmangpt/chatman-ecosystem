import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_closure.subject import Subject
from scripts.measure_train.process_intelligence_closure.methodology import MethodologyCoverage,REQUIRED
from scripts.measure_train.process_intelligence_closure.evidence import RailEvidence,RAILS
from scripts.measure_train.process_intelligence_closure.distributed import RegionWitness
from scripts.measure_train.process_intelligence_closure.qualify import qualify
from scripts.measure_train.process_intelligence_closure.replay import replay

class T(unittest.TestCase):
    def test_full_process_closure_is_bounded_and_replayable(self):
        s=Subject("o/r","a"*40); now=datetime.now(timezone.utc); d="1"*64
        evidence=tuple(RailEvidence(s,r,r.lower(),d,"PASS",r,now) for r in RAILS)
        regions=(RegionWitness(s,"us-west","h1",d,now),RegionWitness(s,"us-east","h2",d,now))
        q=qualify(s,MethodologyCoverage(REQUIRED),evidence,regions,now)
        self.assertEqual(q["census"]["obligations"],())
        self.assertEqual(q["standing"],"PARTIAL_ALIVE")
        self.assertFalse(q["actuation_performed"])
        self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
