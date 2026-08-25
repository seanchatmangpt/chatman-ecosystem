import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_closure.subject import Subject
from scripts.measure_train.process_intelligence_closure.methodology import MethodologyCoverage,REQUIRED
from scripts.measure_train.process_intelligence_closure.evidence import RailEvidence,RAILS
from scripts.measure_train.process_intelligence_closure.closure import closure_census

class T(unittest.TestCase):
    def test_missing_rail_is_exact_obligation(self):
        s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
        rows=tuple(RailEvidence(s,r,r.lower(),"1"*64,"PASS",r,now) for r in RAILS if r!="REPLAY")
        c=closure_census(MethodologyCoverage(REQUIRED),rows,"CURRENT")
        self.assertIn("RAIL:REPLAY",c["obligations"])
