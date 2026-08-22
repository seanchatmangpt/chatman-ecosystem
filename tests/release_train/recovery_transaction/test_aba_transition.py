import unittest
from scripts.release_train.recovery_transaction import *
S=Subject('seanchatmangpt/chatman-ecosystem','3'*40); H='a'*64
def c(g,cut):return RecoveryContext(S,g,cut,H,H,'LATEST_COMPLETE')
class T(unittest.TestCase):
 def test_aba_detected(self):
  ts=[ContextTransition(c(1,'A'),c(2,'B')),ContextTransition(c(2,'B'),c(3,'A'))];self.assertTrue(detect_aba(ts));
  with self.assertRaisesRegex(Refusal,'ABA_RECOVERY_CONTEXT'):require_no_aba(ts)
 def test_non_aba(self):self.assertFalse(detect_aba([ContextTransition(c(1,'A'),c(2,'B'))]))
if __name__=='__main__':unittest.main()
