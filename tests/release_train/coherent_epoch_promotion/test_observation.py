import unittest
from datetime import datetime, timezone, timedelta
from scripts.release_train.coherent_epoch_promotion.subject import Subject
from scripts.release_train.coherent_epoch_promotion.epoch import EpochStamp
from scripts.release_train.coherent_epoch_promotion.observation import Observation,Scope,Outcome
class T(unittest.TestCase):
 def test_pre_epoch_refuses(self):
  t=datetime.now(timezone.utc); s=Subject.parse('o/r@'+'a'*40); e=EpochStamp(s,1,'e','b'*64,t)
  with self.assertRaisesRegex(ValueError,'PRE_EPOCH'): Observation(s,e,Scope.REPOSITORY,Outcome.PASS,'x',t-timedelta(seconds=1))
