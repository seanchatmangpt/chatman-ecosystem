import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import unittest
from scripts.release_train.process_intelligence_crown_admission import PowlModel,bounded_traces,TraceWitness,require_complete,Refused
D="b"*64
class TestPowlOracle(unittest.TestCase):
    def model(self):
        return PowlModel(("S","A","B","T"),frozenset(),frozenset({("S","A"),("S","B"),("A","T"),("B","T")}),"S","T",4)
    def test_sound_complete_reference(self):
        traces=bounded_traces(self.model())
        self.assertEqual({("S","A","T"),("S","B","T")},set(traces))
        require_complete(traces,TraceWitness("BEAM",traces,D))
    def test_extra_trace_refuses_soundness(self):
        traces=bounded_traces(self.model())
        with self.assertRaises(Refused): require_complete(traces,TraceWitness("BAD",traces+(("S","T"),),D))
if __name__=="__main__": unittest.main()
