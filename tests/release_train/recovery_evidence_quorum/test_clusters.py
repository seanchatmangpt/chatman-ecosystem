import unittest
from datetime import datetime,timezone
from scripts.release_train.recovery_evidence_quorum.source import EvidenceSource
from scripts.release_train.recovery_evidence_quorum.witness import RecoveryWitness
from scripts.release_train.recovery_evidence_quorum.independence import IndependenceEvidence
from scripts.release_train.recovery_evidence_quorum.provenance import ProvenanceGraph
from scripts.release_train.recovery_evidence_quorum.clusters import correlated_clusters
class T(unittest.TestCase):
 def test_collapse(self):
  t=datetime.now(timezone.utc); ws=[RecoveryWitness("a",EvidenceSource("p",str(i),str(i),"f"),str(i),"PASS","REPOSITORY",t) for i in range(3)]
  self.assertEqual(len(correlated_clusters(ws,IndependenceEvidence(),ProvenanceGraph())),1)
