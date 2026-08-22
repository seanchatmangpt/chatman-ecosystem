import unittest
from datetime import datetime, timezone, timedelta
from scripts.measure_train.admission import admit
from scripts.measure_train.evidence import *
from scripts.measure_train.identity import *
from scripts.measure_train.window import Window
class AdmissionCourt(unittest.TestCase):
    def setUp(self):
        self.s=Subject("o/r","a"*40); self.w=Window(datetime(2026,8,22,4,tzinfo=timezone.utc),datetime(2026,8,22,6,tzinfo=timezone.utc)); self.now=datetime(2026,8,22,6,tzinfo=timezone.utc)
    def row(self,**kw): return Evidence(kw.get('id','ci'),kw.get('s',self.s),EvidenceKind.CI,kw.get('t','2026-08-22T05:00:00Z'),kw.get('o',Outcome.PASS),detail=kw.get('d',''))
    def test_foreign_refuses(self):
        with self.assertRaises(Refused): admit(self.s,[self.row(s=Subject('o/x','b'*40))],self.w,self.now,timedelta(hours=3))
    def test_conflict_refuses(self):
        with self.assertRaises(Refused): admit(self.s,[self.row(d='a'),self.row(d='b')],self.w,self.now,timedelta(hours=3))
    def test_outside_counted(self): self.assertEqual(admit(self.s,[self.row(t='2026-08-22T03:59:59Z')],self.w,self.now,timedelta(hours=3)).excluded_out_of_window,1)
if __name__=='__main__': unittest.main()
