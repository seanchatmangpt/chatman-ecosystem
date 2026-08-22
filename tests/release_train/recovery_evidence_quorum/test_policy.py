import unittest
from datetime import datetime,timezone
from scripts.release_train.recovery_evidence_quorum.source import EvidenceSource
from scripts.release_train.recovery_evidence_quorum.witness import RecoveryWitness
from scripts.release_train.recovery_evidence_quorum.policy import QuorumPolicy,standing_for
class T(unittest.TestCase):
 def w(self,e,o="PASS"):return RecoveryWitness("a",EvidenceSource(e,e,e,e),e,o,"REPOSITORY",datetime.now(timezone.utc))
 def test_two_clusters_partial(self): self.assertEqual(standing_for(((self.w("1"),),(self.w("2"),)),QuorumPolicy(2),()),"PARTIAL_ALIVE")
 def test_fail_dominates(self): self.assertEqual(standing_for(((self.w("1","FAIL"),),),QuorumPolicy(),()),"BUILD_BROKEN")
