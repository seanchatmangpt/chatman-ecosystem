import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.release_train.fusion_acquisition_admission.subject import Subject
from scripts.release_train.fusion_acquisition_admission.dependency import DependencyGraph
from scripts.release_train.fusion_acquisition_admission.standing import bounded_standing
from scripts.release_train.fusion_acquisition_admission.topology import FusionTopology
class TestDeps(unittest.TestCase):
    def test_red_propagates(self):
        r=Subject("o/r@"+"f"*40); d=Subject("o/d@"+"1"*40); g=DependencyGraph(); g.add(d,standing="BUILD_BROKEN"); g.add(r,[d],standing="UNKNOWN"); blockers=g.blockers(r); self.assertEqual(len(blockers),1); self.assertEqual(bounded_standing(FusionTopology.HEALTHY,blockers)[0],"BLOCKED")
