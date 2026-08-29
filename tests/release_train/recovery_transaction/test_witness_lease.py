import unittest
from datetime import datetime,timedelta,timezone
from scripts.release_train.recovery_transaction import Lease,CompatibilityWitness,WitnessKind,Refusal
H='a'*64; B='b'*64
class T(unittest.TestCase):
 def test_half_open(self):
  n=datetime.now(timezone.utc); l=Lease(n,n+timedelta(minutes=1)); self.assertTrue(l.active(n)); self.assertFalse(l.active(l.expires_at))
 def test_false_exact(self):
  with self.assertRaisesRegex(Refusal,'FALSE_EXACT'): CompatibilityWitness(H,B,WitnessKind.EXACT,H,True)
if __name__=='__main__':unittest.main()
