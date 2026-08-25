import unittest
from datetime import datetime,timezone
from scripts.measure_train.delta.projection import to_ocel_event
class T(unittest.TestCase):
 def test_exact_subject_projection(self):
  e=to_ocel_event('o/r','a'*40,'ci',datetime(2026,1,1,tzinfo=timezone.utc),'PASS'); self.assertEqual(e['ocel:objects'][0]['id'],'o/r@'+'a'*40)
