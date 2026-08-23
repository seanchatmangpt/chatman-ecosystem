import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_trace_relation_msa.subject import Subject,Refused
from scripts.measure_train.process_trace_relation_msa.relation import Relation
from scripts.measure_train.process_trace_relation_msa.case import LabeledCase
from scripts.measure_train.process_trace_relation_msa.sensor import relation_sensor
class T(unittest.TestCase):
 def test_duplicate_refusal(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  c=LabeledCase(s,"1",Relation.EXACT,True,True,"identity","impl",now)
  with self.assertRaises(Refused): relation_sensor([c,c])
