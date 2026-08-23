import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.replicated_evidence_state.authority import ActionClass
from scripts.develop_train.replicated_evidence_state.engine import ReplicatedEvidenceEngine
from scripts.develop_train.replicated_evidence_state.lease import Lease
from scripts.develop_train.replicated_evidence_state.replica_state import ReplicaState
from scripts.develop_train.replicated_evidence_state.replay import replay
from scripts.develop_train.replicated_evidence_state.vector_clock import VectorClock

def state(replica,value,g=3): return ReplicaState(replica,"o/r@"+"a"*40,g,value*64,VectorClock.from_dict({replica:g}))
class EngineTest(unittest.TestCase):
    def test_quorum_receipt_replay_and_split_brain(self):
        now=datetime(2026,8,22,tzinfo=timezone.utc); lease=Lease(now-timedelta(seconds=1),now+timedelta(seconds=10)); e=ReplicatedEvidenceEngine()
        q=e.qualify([state("a","b"),state("b","b"),state("c","c",2)],lease,now,ActionClass.CONSTRUCT)
        self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertFalse(q.receipt.actuation_performed); self.assertTrue(replay(q.receipt,q.receipt.digest()))
        split=e.qualify([state("a","b"),state("b","c")],lease,now)
        self.assertEqual(split.standing,"UNKNOWN"); self.assertIsNone(split.receipt)
