import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.release_train.fusion_acquisition_admission.acquisition import AcquisitionCandidate,Strategy,select
from scripts.release_train.fusion_acquisition_admission.pareto import frontier
class TestAcquire(unittest.TestCase):
    def test_strategies_and_pareto(self):
        a=AcquisitionCandidate("info","9/10",1,10,10); b=AcquisitionCandidate("ind","3/4",3,12,8); c=AcquisitionCandidate("cheap","3/4",1,2,5)
        self.assertEqual(select([a,b,c],Strategy.MAX_INDEPENDENCE).candidate_id,"ind"); self.assertEqual(select([a,b,c],Strategy.MIN_COST).candidate_id,"cheap"); ids={x.candidate_id for x in frontier([a,b,c])}; self.assertIn("info",ids); self.assertIn("ind",ids)
