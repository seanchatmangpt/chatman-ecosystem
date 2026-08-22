import unittest
from datetime import datetime,timedelta,timezone
from scripts.release_train.recovery_transaction import *
H='a'*64; P='b'*64; F='c'*64
class T(unittest.TestCase):
 def test_current_recovery_and_concurrent_move(self):
  now=datetime.now(timezone.utc); s=Subject('seanchatmangpt/chatman-ecosystem','5'*40); before=RecoveryContext(s,1,'A',P,F,'LATEST_COMPLETE'); current=RecoveryContext(s,2,'B',P,F,'LATEST_COMPLETE'); lease=Lease(now,now+timedelta(minutes=5)); attempt=RecoveryAttempt(s,before.digest,current.digest,7,'nonce',now,lease); witness=CompatibilityWitness(before.digest,current.digest,WitnessKind.SEMANTIC_EQUIVALENT,H,True); g=DependencyGraph({s.exact_id:()}); ledger=IdempotencyLedger()
  q=qualify(attempt=attempt,current=current,witness=witness,strategy='VALIDATE_REBIND',at=now,transitions=[ContextTransition(before,current)],graph=g,root=s.exact_id,standings={s.exact_id:'PARTIAL_ALIVE'},need=PersistenceNeed(transactional=True),ledger=ledger)
  self.assertEqual(q.standing,'REQUALIFYING');self.assertEqual(q.store,'SQLITE');self.assertEqual(q.phases,('VERIFY','CONSTRUCT'));self.assertTrue(q.receipt.replay());self.assertFalse(q.receipt.body['actuation_performed'])
  moved=RecoveryContext(s,3,'C',P,F,'LATEST_COMPLETE')
  with self.assertRaisesRegex(Refusal,'STALE_TARGET'):qualify(attempt=attempt,current=moved,witness=witness,strategy='VALIDATE_REBIND',at=now,transitions=[ContextTransition(current,moved)],graph=g,root=s.exact_id,standings={s.exact_id:'PARTIAL_ALIVE'},need=PersistenceNeed(),ledger=IdempotencyLedger())
 def test_aba_blocks_even_if_name_returns(self):
  now=datetime.now(timezone.utc); s=Subject('seanchatmangpt/chatman-ecosystem','6'*40); a=RecoveryContext(s,1,'A',P,F,'LATEST_COMPLETE');b=RecoveryContext(s,2,'B',P,F,'LATEST_COMPLETE');a2=RecoveryContext(s,3,'A',P,F,'LATEST_COMPLETE'); lease=Lease(now,now+timedelta(minutes=5));attempt=RecoveryAttempt(s,a.digest,a2.digest,1,'aba',now,lease);g=DependencyGraph({s.exact_id:()})
  with self.assertRaisesRegex(Refusal,'ABA_RECOVERY_CONTEXT'):qualify(attempt=attempt,current=a2,witness=None,strategy='CAS_RESELECT',at=now,transitions=[ContextTransition(a,b),ContextTransition(b,a2)],graph=g,root=s.exact_id,standings={s.exact_id:'PARTIAL_ALIVE'},need=PersistenceNeed(),ledger=IdempotencyLedger())
if __name__=='__main__':unittest.main()
