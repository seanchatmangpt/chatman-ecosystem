import unittest
from datetime import datetime,timezone
from scripts.measure_train.fusion_realization_msa.subject import Subject,Refused
from scripts.measure_train.fusion_realization_msa.plan import FusionPlan
from scripts.measure_train.fusion_realization_msa.frontier import CalibrationFrontier
from scripts.measure_train.fusion_realization_msa.receipt import manufacture_receipt
from scripts.measure_train.fusion_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_tamper_refuses(self):
  s=Subject("o/r","a"*40); p=FusionPlan(s,"p","1"*64,("x",),.1,1,10,datetime.now(timezone.utc)); f=CalibrationFrontier("p",1,"1"*64)
  r=manufacture_receipt(s,p,f,(("x",1),),"UNKNOWN"); self.assertEqual(replay(r),"REPLAY_MATCH")
  r["body"]["actuation_performed"]=True
  with self.assertRaises(Refused): replay(r)
