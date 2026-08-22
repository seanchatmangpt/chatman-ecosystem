import unittest
from datetime import datetime, timezone, timedelta
from scripts.release_train.ack_discharge_promotion.subject import Subject
from scripts.release_train.ack_discharge_promotion.invalidation import Invalidation
from scripts.release_train.ack_discharge_promotion.graph import DependencyGraph
from scripts.release_train.ack_discharge_promotion.witness import Witness
from scripts.release_train.ack_discharge_promotion.admission import admit, AdmissionRefusal
A=Subject.parse("o/a@"+"a"*40); B=Subject.parse("o/b@"+"b"*40); T=datetime(2026,1,1,tzinfo=timezone.utc)
class X(unittest.TestCase):
    def test_gap_refuses(self):
        inv=Invalidation(A,"e","BUILD_BROKEN",T); graph=DependencyGraph(((A,B),))
        with self.assertRaises(AdmissionRefusal): admit(inv,graph,(Witness(B,"e","ACKNOWLEDGED",T+timedelta(seconds=1)),))
