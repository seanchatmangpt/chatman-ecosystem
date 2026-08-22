import unittest
from datetime import datetime, timezone
from scripts.release_train.ack_discharge_promotion.subject import Subject
from scripts.release_train.ack_discharge_promotion.invalidation import Invalidation
from scripts.release_train.ack_discharge_promotion.graph import DependencyGraph
from scripts.release_train.ack_discharge_promotion.census import census
A=Subject.parse("o/a@"+"a"*40); B=Subject.parse("o/b@"+"b"*40)
class T(unittest.TestCase):
    def test_pending(self):
        rows=census(Invalidation(A,"e","BLOCKED",datetime.now(timezone.utc)),DependencyGraph(((A,B),)),{})
        self.assertEqual(rows[0].state,"PENDING_DELIVERY")
