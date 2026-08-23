import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_closure.subject import Subject
from scripts.measure_train.process_intelligence_closure.distributed import RegionWitness,distributed_currentness

class T(unittest.TestCase):
    def test_multi_region_divergence(self):
        s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
        rows=(RegionWitness(s,"us-west","h1","1"*64,now),RegionWitness(s,"us-east","h2","2"*64,now))
        self.assertEqual(distributed_currentness(s,rows,now,60)["state"],"DIVERGED")
