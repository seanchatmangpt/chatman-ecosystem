import unittest
from datetime import datetime,timezone
from scripts.measure_train.invalidation_ack.subject import Subject,Refused
from scripts.measure_train.invalidation_ack.discharge import Discharge
class T(unittest.TestCase):
 def test_result_bounded(self):
  with self.assertRaises(Refused): Discharge("e",Subject("o/r","a"*40),"a","ALIVE",datetime.now(timezone.utc),"p")
