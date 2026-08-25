import unittest
from scripts.release_train.transport_invariance_crown import *

class ChicagoQualificationCourt(unittest.TestCase):
    def fixture(self, broken=False):
        subject=Subject('seanchatmangpt/chatman-ecosystem','a'*40,'b'*64)
        cal=(Calibration(9,100,0.02,0.1,'c'*64),)
        strata=tuple(Stratum(m,'BEAM','us-west','root',5,0.02,True) for m in REQUIRED_METHODS)
        triple=('s'*64,'t'*64,'o'*64)
        engines=(EngineEvidence('BEAM','impl-a','model-a',*triple),EngineEvidence('WASM','impl-b','model-b',*triple))
        oracles=(OracleEvidence('POWL','oracle-a','formal-a','p'*64),OracleEvidence('OCEL','oracle-b','formal-b','q'*64))
        regions=(RegionEvidence('h1','us-west','1'*64,True,9),RegionEvidence('h2','eu-west','2'*64,True,9))
        failures={k:True for k in REQUIRED_FAILURES}
        graph={'root':('engine',),'engine':()}; standings={'engine':'BUILD_BROKEN' if broken else 'ALIVE'}
        candidates=(Candidate('robust',0.02,0.8,0.1,10),Candidate('wide',0.03,0.9,0.2,8))
        return dict(subject=subject,generation=9,calibrations=cal,miss_limit=0.05,drift_values=(0.01,0.02),strata=strata,methods=set(REQUIRED_METHODS),engines=engines,oracles=oracles,regions=regions,failure_worlds=failures,dependency_graph=graph,dependency_standing=standings,dependency_root='root',candidates=candidates,strategy='MINIMAX',evidence_digest='e'*64)
    def test_full_positive_ceiling_replay_and_failure_dominance(self):
        q=qualify(**self.fixture()); self.assertEqual(q.standing,'PARTIAL_ALIVE'); self.assertIsNotNone(q.receipt); self.assertEqual(replay(q.receipt),'REPLAY_MATCH')
        b=qualify(**self.fixture(broken=True)); self.assertEqual(b.standing,'BUILD_BROKEN'); self.assertIsNone(b.receipt)
        bad=self.fixture(); bad['methods']={'discovery'}
        with self.assertRaisesRegex(Refused,'INCOMPLETE_METHODOLOGY_CLOSURE'): qualify(**bad)
