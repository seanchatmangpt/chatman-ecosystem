import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.invalidation import detect_invalidations
from scripts.measure_train.evidence import *
from scripts.measure_train.identity import Subject
class InvalidationCourt(unittest.TestCase):
    def test_kind_specific_ttl(self):
        r=Evidence('ci',Subject('o/r','a'*40),EvidenceKind.CI,'2026-08-22T04:00:00Z',Outcome.PASS)
        got=detect_invalidations((r,),datetime(2026,8,22,6,tzinfo=timezone.utc),{'ci':timedelta(hours=1)})
        self.assertEqual(got[0].reason,'TTL_EXPIRED')
    def test_unknown_kind_has_no_invented_ttl(self):
        r=Evidence('r',Subject('o/r','a'*40),EvidenceKind.RUNTIME,'2026-08-22T04:00:00Z',Outcome.PASS)
        self.assertEqual(detect_invalidations((r,),datetime(2026,8,22,6,tzinfo=timezone.utc),{}),())
if __name__=='__main__': unittest.main()
