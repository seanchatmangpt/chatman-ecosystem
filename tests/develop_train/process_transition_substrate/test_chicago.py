import unittest,hashlib
from scripts.develop_train.process_transition_substrate import *
class T(unittest.TestCase):
 def test_full(self):
  s=SubjectEpoch("seanchatmangpt/chatman-ecosystem@"+"5"*40,7)
  obs=[Obligation("semantic",State.PASS,"oracle"),Obligation("reactor",State.PASS,"ci"),Obligation("projection",State.PASS,"ci"),Obligation("distributed",State.UNSUPPORTED,"bounded")]
  q=qualify(s.subject,s.generation,obs,hashlib.sha256(b"obligations").hexdigest())
  self.assertEqual(q.standing,"PARTIAL_ALIVE")
  self.assertEqual(replay(q.receipt,q.receipt.digest()),"REPLAY_MATCH")
  self.assertFalse(q.receipt.actuation_performed)
