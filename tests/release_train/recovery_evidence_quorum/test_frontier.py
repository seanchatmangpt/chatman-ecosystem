import unittest
from datetime import datetime,timezone,timedelta
from scripts.release_train.recovery_evidence_quorum.source import EvidenceSource
from scripts.release_train.recovery_evidence_quorum.witness import RecoveryWitness
from scripts.release_train.recovery_evidence_quorum.frontier import current_witnesses
class T(unittest.TestCase):
 def test_future_refuses(self):
  w=RecoveryWitness("a",EvidenceSource("p","r","a","f"),"e","PASS","REPOSITORY",datetime.now(timezone.utc)+timedelta(seconds=5))
  with self.assertRaisesRegex(ValueError,"FUTURE_EVIDENCE"): current_witnesses([w],"a",datetime.now(timezone.utc))
