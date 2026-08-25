import unittest
from scripts.release_train.process_trace_crown import Event, Relation, Subject, Trace, witness
from scripts.release_train.process_trace_crown.refusal import Refused

class TestIdentityRelations(unittest.TestCase):
    def setUp(self):
        self.s = Subject("seanchatmangpt/chatman-ecosystem", "1"*40, "2"*40)
    def test_exact_activity_stutter_noncollapse(self):
        a = Event("A","o1"); b = Event("B","o1")
        left = Trace(self.s,"BEAM",(a,a,b)); right = Trace(self.s,"WASM",(a,b))
        self.assertFalse(witness(left,right,Relation.EXACT,5).accepted)
        self.assertFalse(witness(left,right,Relation.ACTIVITY,5).accepted)
        self.assertTrue(witness(left,right,Relation.STUTTER,5).accepted)
    def test_short_sha_refuses(self):
        with self.assertRaises(Refused): Subject("a/b","abc","2"*40)
