import unittest
from datetime import datetime, timezone
from scripts.develop_train.recovery_evidence_quorum.subject import Subject
from scripts.develop_train.recovery_evidence_quorum.recovery import RecoveryContext, RecoveryAttempt
from scripts.develop_train.recovery_evidence_quorum.evidence import EvidenceSource, RecoveryWitness, WitnessOutcome
from scripts.develop_train.recovery_evidence_quorum.provenance import ProvenanceGraph
from scripts.develop_train.recovery_evidence_quorum.independence import IndependenceEvidence
from scripts.develop_train.recovery_evidence_quorum.policy import QuorumPolicy, Standing
from scripts.develop_train.recovery_evidence_quorum.dependencies import DependencyGraph
from scripts.develop_train.recovery_evidence_quorum.storage import PersistenceNeed
from scripts.develop_train.recovery_evidence_quorum.engine import qualify_recovery
from scripts.develop_train.recovery_evidence_quorum.receipt import replay

class TestE2E(unittest.TestCase):
    def test_correlated_green_does_not_qualify_but_independent_quorum_does(self):
        now=datetime(2026,1,2,tzinfo=timezone.utc); s=Subject('o/r','a'*40); c=RecoveryContext(s,3,'cut','b'*64,'c'*64); a=RecoveryAttempt(s,c.digest,c.digest,1,now,'n')
        def w(e,run,artifact,family): return RecoveryWitness(e,s,a.attempt_id,EvidenceSource('ci',run,artifact*64,family),'recovery',WitnessOutcome.PASS,now)
        x,y=w('x','1','d','gha'),w('y','2','e','gha'); deps=DependencyGraph(); prov=ProvenanceGraph()
        q=qualify_recovery(a,(x,y),now=now,provenance=prov,independence=(),policy=QuorumPolicy(),dependencies=deps,dependency_standings={})
        self.assertEqual(q.standing,Standing.UNKNOWN); self.assertTrue(replay(q.receipt,q.receipt.digest))
        proof=IndependenceEvidence('x','y','f'*64)
        q2=qualify_recovery(a,(x,y),now=now,provenance=prov,independence=(proof,),policy=QuorumPolicy(),dependencies=deps,dependency_standings={},persistence=PersistenceNeed(transactional=True))
        self.assertEqual(q2.standing,Standing.PARTIAL_ALIVE); self.assertEqual(q2.receipt.store,'SQLITE'); self.assertFalse(q2.receipt.actuation_performed)
