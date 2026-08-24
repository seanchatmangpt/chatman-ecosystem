import unittest
from fractions import Fraction as F
from dataclasses import replace
from scripts.release_train.kantorovich_dual_crown import *
class T(unittest.TestCase):
    def fixture(self,blockerset=()):
        s=Subject("o/r","b"*40,"process",7); p=FiniteMeasure.of({"a":1}); q=FiniteMeasure.of({"b":1})
        m=GroundMetric.of(("a","b"),((0,2),(2,0))); plan=TransportPlan.of([("a","b",1)]); dual=DualPotential.of({"a":1},{"b":1})
        oa=OracleWitness("solver-a","model-a",F(2)); ob=OracleWitness("solver-b","model-b",F(2))
        amb=AmbiguitySet("W1",F(1,10),7); rw=RobustWitness(F(1),F(3,2),F(1,10),"witness1")
        cal=Calibration(7,100,F(1,20),F(1,50),"calib123")
        eng=[EngineWitness("BEAM","beam","m1","s","t","o"),EngineWitness("WASM","wasm","m2","s","t","o")]
        ors=[SemanticOracle("POWL","powl","pm","d1"),SemanticOracle("OCEL","ocel","om","d2")]
        regs=[RegionWitness("h1","r1",True,"certcert",7),RegionWitness("h2","r2",True,"certcert",7)]
        worlds={"node","partition","latency","loss","version","certificate","ambiguous_do"}
        return dict(subject=s,source=p,target=q,metric=m,plan=plan,dual=dual,oracle_a=oa,oracle_b=ob,ambiguity=amb,robust=rw,calibration=cal,methods=REQUIRED,engines=eng,oracles=ors,regions=regs,failures=worlds,dependency_blockers=blockerset)
    def test_full_bounded_qualification_and_replay(self):
        q,r=qualify(**self.fixture()); self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertEqual(replay(r),"REPLAY_MATCH")
        with self.assertRaises(Refused): replay(replace(r,digest="0"*64))
    def test_red_dependency_suppresses_receipt(self):
        q,r=qualify(**self.fixture({"BUILD_BROKEN:gall"})); self.assertEqual(q.standing,"BUILD_BROKEN"); self.assertIsNone(r)
