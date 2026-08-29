import unittest
from datetime import datetime, timezone
from scripts.release_train.coherent_epoch_promotion.subject import Subject
from scripts.release_train.coherent_epoch_promotion.epoch import EpochStamp
from scripts.release_train.coherent_epoch_promotion.observation import Observation,Scope,Outcome
from scripts.release_train.coherent_epoch_promotion.census import census
class T(unittest.TestCase):
 def test_focused_pass_not_positive(self):
  t=datetime.now(timezone.utc); s=Subject.parse('o/r@'+'a'*40); e=EpochStamp(s,1,'e','b'*64,t); o=Observation(s,e,Scope.FOCUSED,Outcome.PASS,'x',t)
  self.assertEqual(census((s,),(o,))[0].state,'UNKNOWN')
