import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_ack.subject import Subject,Refused
from scripts.measure_train.invalidation_ack.event import Invalidation
class T(unittest.TestCase):
 def test_new_receipt_requires_digest(self):
  s=Subject("o/r","a"*40)
  with self.assertRaises(Refused): Invalidation(s,"e","NEW_RECEIPT",datetime.now(timezone.utc))
