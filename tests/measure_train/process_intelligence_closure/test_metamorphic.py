import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_closure.subject import Subject
from scripts.measure_train.process_intelligence_closure.evidence import RailEvidence
from scripts.measure_train.process_intelligence_closure.correspondence import rail_equivalence

class T(unittest.TestCase):
    def test_order_invariant(self):
        s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
        rows=[RailEvidence(s,"SEMANTIC","a","1"*64,"PASS","1",now),RailEvidence(s,"POWL","b","1"*64,"PASS","2",now)]
        self.assertEqual(rail_equivalence(rows),rail_equivalence(tuple(reversed(rows))))
