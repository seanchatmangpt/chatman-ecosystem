import unittest
from datetime import datetime, timezone
from scripts.release_train.coherent_epoch_promotion.subject import Subject
from scripts.release_train.coherent_epoch_promotion.epoch import EpochStamp
from scripts.release_train.coherent_epoch_promotion.observation import Observation,Scope,Outcome
from scripts.release_train.coherent_epoch_promotion.cut import EvidenceCut
class T(unittest.TestCase):
 def test_torn_observation_refuses(self):
  t=datetime.now(timezone.utc); s=Subject.parse('o/r@'+'a'*40); e1=EpochStamp(s,1,'e1','b'*64,t); e2=EpochStamp(s,2,'e2','c'*64,t); o=Observation(s,e1,Scope.REPOSITORY,Outcome.PASS,'x',t)
  with self.assertRaisesRegex(ValueError,'TORN_CUT'): EvidenceCut(t,(e2,),(o,))
