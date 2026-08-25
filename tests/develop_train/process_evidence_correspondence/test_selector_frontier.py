import unittest
from scripts.develop_train.process_evidence_correspondence import CompositionCalibration, Refused, current_calibrations, select

class TestSelectorFrontier(unittest.TestCase):
    def test_selector_families_disagree_lawfully(self):
        items=[CompositionCalibration("CONSERVATIVE",5,20,19,.35,.01),CompositionCalibration("INDEPENDENT",5,20,17,.12,.12)]
        _, current=current_calibrations(items)
        self.assertEqual(select(current,"MAX_COVERAGE").mode,"CONSERVATIVE")
        self.assertEqual(select(current,"MIN_WIDTH").mode,"INDEPENDENT")
        self.assertEqual(select(current,"MINIMAX_MISS").mode,"CONSERVATIVE")
        self.assertEqual(select(current,"ROBUST_DEFAULT").mode,"CONSERVATIVE")

    def test_divergent_current_calibration_refuses(self):
        left=CompositionCalibration("CONSERVATIVE",1,5,5,.2,0)
        right=CompositionCalibration("CONSERVATIVE",1,5,4,.2,0)
        with self.assertRaises(Refused):
            current_calibrations([left,right])

if __name__ == "__main__": unittest.main()
