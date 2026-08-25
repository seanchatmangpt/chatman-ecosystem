import unittest
from datetime import datetime,timezone
from scripts.measure_train.requalification_epoch.subject import Subject
from scripts.measure_train.requalification_epoch.witness import Witness
from scripts.measure_train.requalification_epoch.contradiction import contradictions
class T(unittest.TestCase):
 def test_terminal_disagreement_visible(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); c=Subject("c/r","b"*40)
  a=Witness(c,p,1,"e","DISCHARGE","x",now,"REQUALIFIED","a"); b=Witness(c,p,1,"e","DISCHARGE","y",now,"BLOCKED","a")
  self.assertEqual(len(contradictions([a,b])),1)
