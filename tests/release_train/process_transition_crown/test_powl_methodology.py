import unittest
from scripts.release_train.process_transition_crown import PowlModel, require_correspondence, require_methods, REQUIRED_METHODS
from scripts.release_train.process_transition_crown.refusal import Refused

class PowlMethodologyTest(unittest.TestCase):
    def test_bounded_reference_equivalence(self):
        model=PowlModel(("a",),{"a":("b","c"),"b":("d",),"c":("d",)},3)
        traces=model.traces()
        self.assertTrue(require_correspondence(set(traces),set(traces)))
    def test_unsound_trace_refuses(self):
        with self.assertRaises(Refused): require_correspondence({("a","x")},{("a","b")})
    def test_full_methodology_required(self):
        self.assertEqual(require_methods(set(REQUIRED_METHODS)),REQUIRED_METHODS)

if __name__=="__main__": unittest.main()
