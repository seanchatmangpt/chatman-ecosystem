import unittest
from datetime import datetime,timezone
from scripts.release_train.recovery_evidence_quorum.source import EvidenceSource
from scripts.release_train.recovery_evidence_quorum.witness import RecoveryWitness
from scripts.release_train.recovery_evidence_quorum.independence import IndependenceEvidence
from scripts.release_train.recovery_evidence_quorum.provenance import ProvenanceGraph
class T(unittest.TestCase):
 def w(self,e,p="p",f="f"):return RecoveryWitness("a",EvidenceSource(p,e,e,f),e,"PASS","REPOSITORY",datetime.now(timezone.utc))
 def test_family_correlated(self): self.assertEqual(IndependenceEvidence().relation(self.w("1"),self.w("2"),ProvenanceGraph()),"CORRELATED")
 def test_explicit_independent(self): self.assertEqual(IndependenceEvidence([("1","2","INDEPENDENT")]).relation(self.w("1"),self.w("2"),ProvenanceGraph()),"INDEPENDENT")
