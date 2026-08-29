import unittest
from scripts.release_train.process_trace_crown import Event, Independence, Relation, Subject, Trace
from scripts.release_train.process_trace_crown.bisimulation import witness
from scripts.release_train.process_trace_crown.refusal import Refused

class TestPartialOrder(unittest.TestCase):
    def test_independent_reorder(self):
        s=Subject("a/b","1"*40,"2"*40); a=Event("A","x"); b=Event("B","y")
        i=Independence.from_pairs([("x","y")])
        self.assertTrue(witness(Trace(s,"BEAM",(a,b)),Trace(s,"WASM",(b,a)),Relation.PARTIAL_ORDER,4,i).accepted)
    def test_fuel_exhaustion(self):
        s=Subject("a/b","1"*40,"2"*40); a=Event("A","x")
        with self.assertRaises(Refused): witness(Trace(s,"BEAM",(a,)),Trace(s,"WASM",(a,)),Relation.EXACT,0)
