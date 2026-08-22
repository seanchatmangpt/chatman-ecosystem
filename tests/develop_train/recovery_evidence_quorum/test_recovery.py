import unittest
from datetime import datetime, timezone
from scripts.develop_train.recovery_evidence_quorum.subject import Subject, Refused
from scripts.develop_train.recovery_evidence_quorum.recovery import RecoveryContext, RecoveryAttempt

class TestRecovery(unittest.TestCase):
    def test_context_and_attempt_are_deterministic(self):
        s=Subject('o/r','a'*40); c=RecoveryContext(s,2,'cut','b'*64,'c'*64)
        self.assertEqual(c.digest, RecoveryContext(s,2,'cut','b'*64,'c'*64).digest)
        a=RecoveryAttempt(s,c.digest,c.digest,1,datetime(2026,1,1,tzinfo=timezone.utc),'n')
        self.assertEqual(a.attempt_id, RecoveryAttempt(s,c.digest,c.digest,1,datetime(2026,1,1,tzinfo=timezone.utc),'n').attempt_id)
        with self.assertRaisesRegex(Refused,'INVALID_RECOVERY_CONTEXT'): RecoveryContext(s,-1,'cut','b'*64,'c'*64)
