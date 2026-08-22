import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.train import measure
from scripts.measure_train.window import Window
from scripts.measure_train.identity import *
from scripts.measure_train.evidence import *
from scripts.measure_train.replay import verify
class TrainCourt(unittest.TestCase):
    def setUp(self): self.s=Subject('o/r','a'*40); self.w=Window(datetime(2026,8,22,4,tzinfo=timezone.utc),datetime(2026,8,22,6,tzinfo=timezone.utc)); self.now=datetime(2026,8,22,6,tzinfo=timezone.utc)
    def test_end_to_end_replay(self):
        row=Evidence('ci',self.s,EvidenceKind.CI,'2026-08-22T05:00:00Z',Outcome.PASS)
        m=measure(self.s,[row],self.w,self.now,timedelta(hours=3)); self.assertEqual(m.standing,Standing.PARTIAL_ALIVE); self.assertTrue(verify(m.receipt,(row,)))
    def test_invalidation_downgrades(self):
        row=Evidence('ci',self.s,EvidenceKind.CI,'2026-08-22T05:00:00Z',Outcome.PASS)
        m=measure(self.s,[row],self.w,self.now,timedelta(hours=3),{'ci':timedelta(minutes=30)}); self.assertEqual(m.standing,Standing.UNKNOWN)
    def test_no_do_authority(self): self.assertEqual(measure(self.s,[],self.w,self.now,timedelta(hours=3)).authority,'OBSERVE_MEASURE_ONLY')
if __name__=='__main__': unittest.main()
