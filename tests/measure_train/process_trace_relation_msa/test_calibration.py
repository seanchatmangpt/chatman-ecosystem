import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_trace_relation_msa.subject import Subject
from scripts.measure_train.process_trace_relation_msa.relation import Relation
from scripts.measure_train.process_trace_relation_msa.case import LabeledCase
from scripts.measure_train.process_trace_relation_msa.calibration import calibrate
class T(unittest.TestCase):
 def test_calibrated_and_false_equivalence(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  good=[LabeledCase(s,str(i),Relation.EXACT,i<3,i<3,"identity","impl",now) for i in range(6)]
  self.assertEqual(calibrate(good,Relation.EXACT).state,"CALIBRATED")
  bad=[LabeledCase(s,"b"+str(i),Relation.EXACT,False,True,"object-drift","impl",now) for i in range(6)]
  self.assertEqual(calibrate(bad,Relation.EXACT).state,"UNRELIABLE")
