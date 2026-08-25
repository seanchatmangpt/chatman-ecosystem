import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.evidence_composition_msa.subject import Subject
from scripts.measure_train.evidence_composition_msa.interval import Interval
from scripts.measure_train.evidence_composition_msa.evidence import EvidenceNode
from scripts.measure_train.evidence_composition_msa.calibration import CompositionCalibration
from scripts.measure_train.evidence_composition_msa.graph import admit_graph
from scripts.measure_train.evidence_composition_msa.blockers import blocker_cut
from scripts.measure_train.evidence_composition_msa.bounded_standing import standing
class T(unittest.TestCase):
 def test_red_parent_is_not_laundered(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc); iv=Interval(Fraction(1,2),Fraction(1))
  bad=EvidenceNode(s,"bad","RUNTIME",1,iv,"c"*64,"d"*64,"r",now,state="FAIL")
  good=EvidenceNode(s,"good","REPLAY",1,iv,"e"*64,"f"*64,"r",now,state="PASS")
  g=admit_graph([bad,good],[("good","bad")]); cut=blocker_cut([bad,good],g)
  cal=CompositionCalibration(10,Fraction(1),Fraction(0),Fraction(1,2),"CALIBRATED")
  self.assertEqual(cut,("bad",)); self.assertEqual(standing([bad,good],cal,True,cut),"BUILD_BROKEN")
