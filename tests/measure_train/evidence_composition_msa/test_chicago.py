import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.evidence_composition_msa.subject import Subject
from scripts.measure_train.evidence_composition_msa.interval import Interval
from scripts.measure_train.evidence_composition_msa.evidence import EvidenceNode
from scripts.measure_train.evidence_composition_msa.calibration import CompositionCalibration
from scripts.measure_train.evidence_composition_msa.methodology import REQUIRED
from scripts.measure_train.evidence_composition_msa.qualify import qualify
from scripts.measure_train.evidence_composition_msa.replay import replay
class T(unittest.TestCase):
 def test_complete_clean_evidence_caps_at_partial_alive(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc); iv=Interval(Fraction(4,5),Fraction(1))
  nodes=[
   EvidenceNode(s,"semantic","SEMANTIC",1,iv,"c"*64,"d"*64,"sem",now),
   EvidenceNode(s,"runtime","RUNTIME",1,iv,"e"*64,"f"*64,"run",now),
   EvidenceNode(s,"replay","REPLAY",1,iv,"1"*64,"2"*64,"rep",now),
  ]
  cal=CompositionCalibration(20,Fraction(19,20),Fraction(1,20),Fraction(1,5),"CALIBRATED")
  q=qualify(s,nodes,[("runtime","semantic"),("replay","runtime")],cal,REQUIRED)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q["actuation_performed"])
  self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
