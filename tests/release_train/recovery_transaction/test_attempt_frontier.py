import unittest
from datetime import datetime,timedelta,timezone
from scripts.release_train.recovery_transaction import *
S=Subject('seanchatmangpt/chatman-ecosystem','2'*40); H='a'*64
N=datetime.now(timezone.utc); L=Lease(N,N+timedelta(hours=1))
def a(o,n):return RecoveryAttempt(S,H,H,o,n,N,L)
class T(unittest.TestCase):
 def test_current_history(self):
  f=AttemptFrontier.build([a(1,'x'),a(2,'y')]); self.assertEqual(f.current.ordinal,2); self.assertEqual(len(f.historical),1)
 def test_divergent_max(self):
  with self.assertRaisesRegex(Refusal,'DIVERGENT'):AttemptFrontier.build([a(2,'x'),a(2,'y')])
if __name__=='__main__':unittest.main()
