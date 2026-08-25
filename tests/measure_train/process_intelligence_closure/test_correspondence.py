import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_closure.subject import Subject
from scripts.measure_train.process_intelligence_closure.evidence import RailEvidence
from scripts.measure_train.process_intelligence_closure.correspondence import rail_equivalence

class T(unittest.TestCase):
    def test_divergence_visible(self):
        s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
        rows=(RailEvidence(s,"PROJECTION","a","1"*64,"PASS","a",now),RailEvidence(s,"PROJECTION","b","2"*64,"PASS","b",now))
        self.assertEqual(rail_equivalence(rows)["divergent"],("PROJECTION",))
