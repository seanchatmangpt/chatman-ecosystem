import unittest
from datetime import datetime, timezone
from scripts.develop_train.recovery_evidence_quorum.evidence import EvidenceSource, RecoveryWitness, WitnessOutcome
from scripts.develop_train.recovery_evidence_quorum.subject import Subject
from scripts.develop_train.recovery_evidence_quorum.independence import EvidenceRelation, IndependenceEvidence, correlated_clusters, relation
from scripts.develop_train.recovery_evidence_quorum.provenance import ProvenanceGraph

def w(e,p,r,a,f): return RecoveryWitness(e,Subject('o/r','a'*40),'x',EvidenceSource(p,r,a*64,f),'recovery',WitnessOutcome.PASS,datetime(2026,1,1,tzinfo=timezone.utc))
class TestIndependence(unittest.TestCase):
    def test_correlated_family_collapses_and_explicit_independence_preserves(self):
        a,b=w('a','ci','1','b','gha'),w('b','ci','2','c','gha')
        g=ProvenanceGraph(); self.assertEqual(relation(a,b,g),EvidenceRelation.CORRELATED)
        self.assertEqual(correlated_clusters((a,b),g),(('a','b'),))
        proof=IndependenceEvidence('a','b','d'*64)
        self.assertEqual(relation(a,b,g,(proof,)),EvidenceRelation.INDEPENDENT)
        self.assertEqual(correlated_clusters((a,b),g,(proof,)),(('a',),('b',)))
