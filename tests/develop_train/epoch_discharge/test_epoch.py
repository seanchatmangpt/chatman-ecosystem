import unittest
from datetime import datetime,timezone
from scripts.develop_train.epoch_discharge.identity import Subject
from scripts.develop_train.epoch_discharge.epoch import InvalidationEpoch
class T(unittest.TestCase):
 def test_generation_and_receipt_are_bounded(self):
  s=Subject("a/b@"+"a"*40); e=InvalidationEpoch(s,3,"evt","b"*64,datetime.now(timezone.utc)); self.assertEqual(e.generation,3)
  with self.assertRaisesRegex(ValueError,"INVALID_GENERATION"): InvalidationEpoch(s,-1,"evt","b"*64,datetime.now(timezone.utc))
