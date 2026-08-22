import unittest
from datetime import datetime, timezone
from scripts.release_train.coherent_epoch_promotion.subject import Subject
from scripts.release_train.coherent_epoch_promotion.epoch import EpochStamp
class T(unittest.TestCase):
 def test_generation(self):
  s=Subject.parse('o/r@'+'a'*40)
  EpochStamp(s,0,'e','b'*64,datetime.now(timezone.utc))
  with self.assertRaisesRegex(ValueError,'INVALID_GENERATION'): EpochStamp(s,-1,'e','b'*64,datetime.now(timezone.utc))
