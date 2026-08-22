import unittest
from dataclasses import replace
from datetime import datetime,timezone,timedelta
from scripts.develop_train.epoch_discharge.identity import Subject
from scripts.develop_train.epoch_discharge.epoch import InvalidationEpoch
from scripts.develop_train.epoch_discharge.receipt import make_receipt,replay
class T(unittest.TestCase):
 def test_tamper_sensitive_and_generation_bound(self):
  e=InvalidationEpoch(Subject("a/p@"+"a"*40),4,"e","b"*64,datetime.now(timezone.utc)-timedelta(seconds=1)); r=make_receipt(e,"ALL","PARTIAL_ALIVE","MEMORY",())
  self.assertTrue(replay(r)); self.assertFalse(replay(replace(r,generation=5)))
