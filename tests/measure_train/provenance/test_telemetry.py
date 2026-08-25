import unittest
from datetime import datetime,timezone
from scripts.measure_train.provenance.subject import Subject
from scripts.measure_train.provenance.source import Source
from scripts.measure_train.provenance.claim import Claim
from scripts.measure_train.provenance.telemetry import project_events
class T(unittest.TestCase):
 def test_binding(self):
  s=Subject("o/r","a"*40); c=Claim(s,Source("RUNTIME","x"),datetime.now(timezone.utc),"PASS","e")
  e=project_events(s,[c],[])[0]; self.assertEqual(e["sha"],s.sha)
