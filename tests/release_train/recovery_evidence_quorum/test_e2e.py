import unittest
from datetime import datetime,timezone
from scripts.release_train.recovery_evidence_quorum.subject import Subject
from scripts.release_train.recovery_evidence_quorum.source import EvidenceSource
from scripts.release_train.recovery_evidence_quorum.witness import RecoveryWitness
from scripts.release_train.recovery_evidence_quorum.independence import IndependenceEvidence
from scripts.release_train.recovery_evidence_quorum.provenance import ProvenanceGraph
from scripts.release_train.recovery_evidence_quorum.policy import QuorumPolicy
from scripts.release_train.recovery_evidence_quorum.dependency import DependencyGraph
from scripts.release_train.recovery_evidence_quorum.engine import qualify
class T(unittest.TestCase):
 def w(self,e,p,f): return RecoveryWitness("attempt",EvidenceSource(p,e,e,f),e,"PASS","REPOSITORY",datetime.now(timezone.utc))
 def test_correlated_greens_unknown_then_independent_partial(self):
  s=Subject("seanchatmangpt/chatman-ecosystem","f"*40)
  ws=[self.w("1","p","fam"),self.w("2","p","fam"),self.w("3","p","fam")]
  now=datetime.now(timezone.utc)
  q=qualify(s,"attempt",ws,now,IndependenceEvidence(),ProvenanceGraph(),QuorumPolicy(2),DependencyGraph(),{},"MEMORY")
  self.assertEqual(q["standing"],"UNKNOWN"); self.assertTrue(q["replay"]); self.assertFalse(q["receipt"]["body"]["actuation_performed"])
  ws=[self.w("1","p1","f1"),self.w("2","p2","f2")]
  now=datetime.now(timezone.utc)
  q=qualify(s,"attempt",ws,now,IndependenceEvidence([("1","2","INDEPENDENT")]),ProvenanceGraph(),QuorumPolicy(2),DependencyGraph(),{},"SQLITE")
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertEqual(q["receipt"]["body"]["store"],"SQLITE")
