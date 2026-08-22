import unittest
from datetime import datetime, timezone, timedelta
from scripts.develop_train.recovery_evidence_quorum.subject import Subject, Refused
from scripts.develop_train.recovery_evidence_quorum.recovery import RecoveryContext, RecoveryAttempt
from scripts.develop_train.recovery_evidence_quorum.evidence import EvidenceSource, RecoveryWitness, WitnessOutcome
from scripts.develop_train.recovery_evidence_quorum.frontier import WitnessFrontier

class TestFrontier(unittest.TestCase):
    def test_foreign_is_historical_and_future_refuses(self):
        s=Subject('o/r','a'*40); other=Subject('o/x','b'*40); c=RecoveryContext(s,1,'c','b'*64,'c'*64); now=datetime(2026,1,2,tzinfo=timezone.utc); a=RecoveryAttempt(s,c.digest,c.digest,1,now-timedelta(hours=1),'n'); src=EvidenceSource('p','r','d'*64,'f')
        good=RecoveryWitness('g',s,a.attempt_id,src,'recovery',WitnessOutcome.PASS,now)
        old=RecoveryWitness('o',other,a.attempt_id,src,'recovery',WitnessOutcome.PASS,now)
        f=WitnessFrontier.build(a,(good,old),now); self.assertEqual(len(f.current),1); self.assertEqual(len(f.historical),1)
        future=RecoveryWitness('f',s,a.attempt_id,src,'recovery',WitnessOutcome.PASS,now+timedelta(seconds=1))
        with self.assertRaisesRegex(Refused,'FUTURE_RECOVERY_EVIDENCE'): WitnessFrontier.build(a,(future,),now)
