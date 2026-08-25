import unittest
from scripts.release_train.kantorovich_dual_crown import *
class T(unittest.TestCase):
    def test_global_gates_and_do(self):
        e=[EngineWitness("BEAM","beam","m1","s","t","o"),EngineWitness("WASM","wasm","m2","s","t","o")]
        self.assertTrue(require_engines(e))
        o=[SemanticOracle("POWL","powl","pm","d1"),SemanticOracle("OCEL","ocel","om","d2")]; self.assertTrue(require_oracles(o))
        r=[RegionWitness("h1","r1",True,"certcert",1),RegionWitness("h2","r2",True,"certcert",1)]; self.assertTrue(require_regions(r))
        with self.assertRaises(Refused): admit("DO")
        self.assertEqual(admit("DO","BRCE"),"DO")
    def test_dependency_cycle(self):
        with self.assertRaises(Refused): blockers({"a":["b"],"b":["a"]},{"a":"ALIVE","b":"ALIVE"})
