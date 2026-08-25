import unittest
from scripts.release_train.process_trace_crown import *

class TestChicago(unittest.TestCase):
    def test_aligned_path_and_failure_dominance(self):
        s=Subject("seanchatmangpt/chatman-ecosystem","1"*40,"2"*40)
        events=(Event("discover","case"),Event("conform","case"))
        beam=Trace(s,"BEAM",events); wasm=Trace(s,"WASM",events)
        oracles=(OracleWitness("ref-a","impl-a",beam),OracleWitness("ref-b","impl-b",wasm))
        rails=tuple(RailEvidence(r,s,beam.digest,"PASS") for r in Rail)
        q=qualify(beam,wasm,relation=Relation.EXACT,fuel=8,oracle_witnesses=oracles,rails=rails,methodologies=set(REQUIRED_METHODOLOGIES),failures=set(Failure),blockers=set())
        self.assertEqual(q.standing,Standing.PARTIAL_ALIVE)
        self.assertIsNotNone(q.receipt)
        replay(q.receipt,q.receipt.digest)
        failed=list(rails); failed[0]=RailEvidence(failed[0].rail,s,beam.digest,"FAIL")
        q2=qualify(beam,wasm,relation=Relation.EXACT,fuel=8,oracle_witnesses=oracles,rails=tuple(failed),methodologies=set(REQUIRED_METHODOLOGIES),failures=set(Failure),blockers=set())
        self.assertEqual(q2.standing,Standing.BUILD_BROKEN)
        self.assertIsNone(q2.receipt)
