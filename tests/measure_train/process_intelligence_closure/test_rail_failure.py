import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_closure.subject import Subject
from scripts.measure_train.process_intelligence_closure.methodology import MethodologyCoverage,REQUIRED
from scripts.measure_train.process_intelligence_closure.evidence import RailEvidence,RAILS
from scripts.measure_train.process_intelligence_closure.closure import closure_census
from scripts.measure_train.process_intelligence_closure.correspondence import rail_equivalence
from scripts.measure_train.process_intelligence_closure.standing import standing

class T(unittest.TestCase):
    def test_one_failed_rail_blocks_crown(self):
        s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
        rows=tuple(RailEvidence(s,r,r.lower(),"1"*64,"FAIL" if r=="REACTOR" else "PASS",r,now) for r in RAILS)
        c=closure_census(MethodologyCoverage(REQUIRED),rows,"CURRENT")
        self.assertEqual(standing(c,rail_equivalence(rows)),"BUILD_BROKEN")
