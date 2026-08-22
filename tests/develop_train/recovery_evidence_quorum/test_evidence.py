import unittest
from datetime import datetime
from scripts.develop_train.recovery_evidence_quorum.evidence import EvidenceSource, RecoveryWitness, WitnessOutcome
from scripts.develop_train.recovery_evidence_quorum.subject import Subject, Refused

class TestEvidence(unittest.TestCase):
    def test_source_fingerprint_and_time_refusal(self):
        src=EvidenceSource('ci','run','b'*64,'gha')
        self.assertEqual(src.fingerprint, EvidenceSource('ci','run','b'*64,'gha').fingerprint)
        with self.assertRaisesRegex(Refused,'NAIVE_WITNESS_TIME'):
            RecoveryWitness('e',Subject('o/r','a'*40),'attempt',src,'recovery',WitnessOutcome.PASS,datetime(2026,1,1))
