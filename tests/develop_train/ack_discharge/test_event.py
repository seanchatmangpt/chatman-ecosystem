import unittest
from datetime import datetime,timezone
from scripts.develop_train.ack_discharge.event import *
from scripts.develop_train.ack_discharge.subject import Subject
class T(unittest.TestCase):
 def test_replacement(self):
  s=Subject('o/r','a'*40)
  with self.assertRaises(RefusedEvent):InvalidationEvent(s,InvalidationKind.NEW_RECEIPT,'e',datetime.now(timezone.utc))
  InvalidationEvent(s,InvalidationKind.NEW_RECEIPT,'e',datetime.now(timezone.utc),'b'*64)
