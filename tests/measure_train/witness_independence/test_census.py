import unittest
from datetime import datetime,timezone
from scripts.measure_train.witness_independence.subject import Subject
from scripts.measure_train.witness_independence.source import EvidenceSource
from scripts.measure_train.witness_independence.observation import WitnessObservation
from scripts.measure_train.witness_independence.census import cluster_census
class T(unittest.TestCase):
 def test_correlated_green_counts_once(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
  rows=[WitnessObservation(s,EvidenceSource("WORKFLOW","same",str(i),"","s"+str(i)),"REPOSITORY","PASS",str(i),now) for i in range(4)]
  census=cluster_census(rows)
  self.assertEqual(len(census),1); self.assertEqual(census[0]["state"],"PASS")
