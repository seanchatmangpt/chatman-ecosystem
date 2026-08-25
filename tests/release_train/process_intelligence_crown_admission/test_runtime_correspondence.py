import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import unittest
from scripts.release_train.process_intelligence_crown_admission import *
D="c"*64; A="d"*64; B="e"*64
class TestRuntimeCorrespondence(unittest.TestCase):
    def test_two_disposable_engines_same_semantics(self):
        p1=Projection(Engine.BEAM,D,frozenset({"x","y"}),A)
        p2=Projection(Engine.WASM,D,frozenset({"x","y"}),B)
        w=DifferentialWitness(p1,p2,TraceWitness("BEAM",(("S","T"),),D),TraceWitness("WASM",(("S","T"),),D))
        require_equivalent((("S","T"),),w)
    def test_obligation_loss_refuses(self):
        p1=Projection(Engine.BEAM,D,frozenset({"x"}),A)
        p2=Projection(Engine.WASM,D,frozenset({"y"}),B)
        with self.assertRaises(Refused): require_correspondence(p1,p2)
if __name__=="__main__": unittest.main()
