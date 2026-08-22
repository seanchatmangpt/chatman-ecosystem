import unittest
from datetime import datetime, timezone, timedelta
from scripts.release_train.ack_discharge_promotion.subject import Subject
from scripts.release_train.ack_discharge_promotion.invalidation import Invalidation
from scripts.release_train.ack_discharge_promotion.graph import DependencyGraph
from scripts.release_train.ack_discharge_promotion.witness import Witness
from scripts.release_train.ack_discharge_promotion.strategy import Strategy
from scripts.release_train.ack_discharge_promotion.engine import qualify
A=Subject.parse("o/a@"+"a"*40); B=Subject.parse("o/b@"+"b"*40); T=datetime(2026,1,1,tzinfo=timezone.utc)
class X(unittest.TestCase):
    def test_complete(self):
        w=(Witness(B,"e","DELIVERED",T),Witness(B,"e","ACKNOWLEDGED",T+timedelta(seconds=1)),Witness(B,"e","DISCHARGED",T+timedelta(seconds=2),"REQUALIFIED"))
        r=qualify(invalidation=Invalidation(A,"e","BLOCKED",T),graph=DependencyGraph(((A,B),)),witnesses=w,strategy=Strategy("ALL"))
        self.assertEqual(r["standing"],"PARTIAL_ALIVE"); self.assertEqual(r["plan"]["phases"],["VERIFY","CONSTRUCT"])
