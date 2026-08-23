import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_correspondence_msa.region import RegionWitness,multi_region_current
class T(unittest.TestCase):
 def test_two_regions(self):
  now=datetime.now(timezone.utc); sem="b"*64
  rows=[RegionWitness("r1","h1",sem,now,True),RegionWitness("r2","h2",sem,now,True)]
  self.assertEqual(multi_region_current(rows,now,10),"CURRENT")
