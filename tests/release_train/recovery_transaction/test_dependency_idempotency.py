import unittest
from scripts.release_train.recovery_transaction import *
class T(unittest.TestCase):
 def test_blocker_propagates(self):
  g=DependencyGraph({'root':('dep',),'dep':()});self.assertEqual(g.blockers('root',{'root':'PARTIAL_ALIVE','dep':'BUILD_BROKEN'}),('dep',))
 def test_cycle(self):
  with self.assertRaisesRegex(Refusal,'CYCLE'):DependencyGraph({'a':('b',),'b':('a',)}).order('a')
 def test_idempotency_conflict(self):
  l=IdempotencyLedger();self.assertTrue(l.admit('k','a'*64));self.assertFalse(l.admit('k','a'*64))
  with self.assertRaisesRegex(Refusal,'IDEMPOTENCY_CONFLICT'):l.admit('k','b'*64)
if __name__=='__main__':unittest.main()
