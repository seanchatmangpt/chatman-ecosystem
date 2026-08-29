import unittest
from scripts.release_train.process_trace_crown import Event, OracleWitness, Rail, RailEvidence, Subject, Trace
from scripts.release_train.process_trace_crown.oracle import require_independent
from scripts.release_train.process_trace_crown.rail import admit
from scripts.release_train.process_trace_crown.refusal import Refused

class TestOracleRails(unittest.TestCase):
    def test_oracle_collusion_refuses(self):
        s=Subject("a/b","1"*40,"2"*40); t=Trace(s,"BEAM",(Event("A","x"),))
        with self.assertRaises(Refused): require_independent((OracleWitness("o1","d",t),OracleWitness("o2","d",t)))
    def test_cross_rail_trace_drift_refuses(self):
        s=Subject("a/b","1"*40,"2"*40)
        rows=(RailEvidence(Rail.CI,s,"a","PASS"),RailEvidence(Rail.REACTOR,s,"b","PASS"))
        with self.assertRaises(Refused): admit(rows)
