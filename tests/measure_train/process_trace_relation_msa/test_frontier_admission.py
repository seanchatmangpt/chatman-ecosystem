import unittest
from scripts.measure_train.process_trace_relation_msa.relation import Relation
from scripts.measure_train.process_trace_relation_msa.frontier import CalibrationFrontier,current_frontier
from scripts.measure_train.process_trace_relation_msa.calibration import RelationCalibration
from scripts.measure_train.process_trace_relation_msa.admission import admit_calibration
from scripts.measure_train.process_trace_relation_msa.subject import Refused
class T(unittest.TestCase):
 def test_current_and_admission(self):
  f=CalibrationFrontier(Relation.EXACT,2,"a"*64,"CALIBRATED")
  self.assertEqual(current_frontier([f])[0],f)
  c=RelationCalibration(Relation.EXACT,10,1,1,0,0.7,"CALIBRATED")
  self.assertEqual(admit_calibration(c,f),"ADMITTED")
  with self.assertRaises(Refused):
   current_frontier([f,CalibrationFrontier(Relation.EXACT,2,"b"*64,"CALIBRATED")])
