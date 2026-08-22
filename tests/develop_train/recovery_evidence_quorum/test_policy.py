import unittest
from datetime import datetime, timezone
from scripts.develop_train.recovery_evidence_quorum.evidence import EvidenceSource, RecoveryWitness, WitnessOutcome
from scripts.develop_train.recovery_evidence_quorum.policy import QuorumPolicy, Standing, evaluate_quorum
from scripts.develop_train.recovery_evidence_quorum.subject import Subject

def w(e,o): return RecoveryWitness(e,Subject('o/r','a'*40),'x',EvidenceSource(e,e,(e[0] if e else 'a')*64,e),'recovery',o,datetime(2026,1,1,tzinfo=timezone.utc))
class TestPolicy(unittest.TestCase):
    def test_quorum_never_manufactures_alive_and_failure_dominates(self):
        ws=(w('aa',WitnessOutcome.PASS),w('bb',WitnessOutcome.PASS))
        self.assertEqual(evaluate_quorum(QuorumPolicy(),ws,(('aa',),('bb',))),Standing.PARTIAL_ALIVE)
        broken=(ws[0],w('cc',WitnessOutcome.FAIL))
        self.assertEqual(evaluate_quorum(QuorumPolicy(),broken,(('aa',),('cc',))),Standing.BUILD_BROKEN)
