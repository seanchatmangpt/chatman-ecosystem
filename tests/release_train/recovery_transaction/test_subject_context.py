import unittest
from scripts.release_train.recovery_transaction import Subject,RecoveryContext,Refusal
H='a'*64; SHA='1'*40
class T(unittest.TestCase):
 def test_exact_and_context_digest(self):
  s=Subject('seanchatmangpt/chatman-ecosystem',SHA); c=RecoveryContext(s,2,'cut-a',H,H,'LATEST_COMPLETE'); self.assertEqual(c.digest,len(c.digest)*c.digest[:0]+c.digest); self.assertEqual(len(c.digest),64)
 def test_inexact_refuses(self):
  with self.assertRaisesRegex(Refusal,'INEXACT_SUBJECT'): Subject('bad','main')
if __name__=='__main__':unittest.main()
