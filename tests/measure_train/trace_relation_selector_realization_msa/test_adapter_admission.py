import unittest
from datetime import datetime,timezone
from scripts.measure_train.trace_relation_selector_realization_msa.adapter import ExternalSelectionReceipt,adapt_external
from scripts.measure_train.trace_relation_selector_realization_msa.frontier import CalibrationFrontier
from scripts.measure_train.trace_relation_selector_realization_msa.admission import admit_decision
from scripts.measure_train.trace_relation_selector_realization_msa.subject import Refused
class T(unittest.TestCase):
 def test_source_authority_and_current_calibration(self):
  now=datetime.now(timezone.utc)
  r=ExternalSelectionReceipt("o/r","a"*40,"b"*64,"MINIMAX_ERROR",2,"c"*64,"d",("EXACT",),("EXACT","ACTIVITY"),100000,5,now,"SELECT",False)
  d=adapt_external(r); f=CalibrationFrontier(d.selector,"d"*64,"CALIBRATED")
  self.assertEqual(admit_decision(d,(f,),now,10),"ADMITTED")
  bad=r.__class__(**{**r.__dict__,"actuation_performed":True})
  with self.assertRaises(Refused): adapt_external(bad)
