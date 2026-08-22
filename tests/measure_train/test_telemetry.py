import unittest
from scripts.measure_train.telemetry import project_ocel
from scripts.measure_train.evidence import *
from scripts.measure_train.identity import Subject
class TelemetryCourt(unittest.TestCase):
    def test_projection_preserves_subject_and_outcome(self):
        s=Subject('o/r','a'*40); e=Evidence('42',s,EvidenceKind.PR,'2026-08-22T05:00:00Z',Outcome.PENDING)
        p=project_ocel((e,))[0]; self.assertEqual(p.object_id,s.identity); self.assertIn(('outcome','PENDING'),p.attributes)
    def test_projection_deterministic(self):
        s=Subject('o/r','a'*40); a=Evidence('b',s,EvidenceKind.CI,'2026-08-22T05:00:00Z',Outcome.PASS); b=Evidence('a',s,EvidenceKind.CI,'2026-08-22T05:00:00Z',Outcome.PASS)
        self.assertEqual(project_ocel((a,b)),project_ocel((b,a)))
if __name__=='__main__': unittest.main()
