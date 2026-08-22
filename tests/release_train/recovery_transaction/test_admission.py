import unittest
from datetime import datetime,timedelta,timezone
from scripts.release_train.recovery_transaction import *
S=Subject('seanchatmangpt/chatman-ecosystem','4'*40); H='a'*64; B='b'*64; N=datetime.now(timezone.utc); L=Lease(N,N+timedelta(hours=1)); C=RecoveryContext(S,2,'B',H,H,'LATEST_COMPLETE')
class T(unittest.TestCase):
 def test_current_cas(self):admit_attempt(RecoveryAttempt(S,B,C.digest,1,'n',N,L),C,None,N,'CAS_RESELECT')
 def test_stale_target(self):
  with self.assertRaisesRegex(Refusal,'STALE_TARGET'):admit_attempt(RecoveryAttempt(S,B,H,1,'n',N,L),C,None,N,'CAS_RESELECT')
 def test_backward_not_rebind(self):
  w=CompatibilityWitness(B,C.digest,WitnessKind.BACKWARD_COMPATIBLE,H,True)
  with self.assertRaisesRegex(Refusal,'EQUIVALENCE'):admit_attempt(RecoveryAttempt(S,B,C.digest,1,'n',N,L),C,w,N,'VALIDATE_REBIND')
if __name__=='__main__':unittest.main()
