import unittest
from fractions import Fraction
from scripts.develop_train.distributional_process_capital.subject import Subject
from scripts.develop_train.distributional_process_capital.calibration import Calibration
from scripts.develop_train.distributional_process_capital.pareto import Candidate
from scripts.develop_train.distributional_process_capital.selectors import Strategy
from scripts.develop_train.distributional_process_capital.methodology import REQUIRED
from scripts.develop_train.distributional_process_capital.correspondence import EngineWitness,RegionWitness
from scripts.develop_train.distributional_process_capital.failures import World
from scripts.develop_train.distributional_process_capital.qualify import qualify
from scripts.develop_train.distributional_process_capital.receipt import replay
class ChicagoCourt(unittest.TestCase):
    def test_full_methodology_robust_capital_and_failure_dominance(self):
        subject=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40+"#"+"b"*64)
        cal=Calibration(5,"d"*64,20,1,Fraction(1,10))
        cand=Candidate("robust",Fraction(1,10),Fraction(1,4),Fraction(1,5),20)
        engines=[EngineWitness("BEAM","i1","m1","s","t","o"),EngineWitness("WASM","i2","m2","s","t","o")]
        regions=[RegionWitness("h1","r1",True,"c1",7),RegionWitness("h2","r2",True,"c2",7)]
        q=qualify(subject,Strategy.MIN_WORST,cal,cand,REQUIRED,engines,regions,list(World))
        self.assertEqual(q.standing,"PARTIAL_ALIVE")
        self.assertEqual(replay(q.receipt,q.receipt.digest),"REPLAY_MATCH")
        red=qualify(subject,Strategy.MIN_WORST,cal,cand,REQUIRED,engines,regions,list(World),dependencies=("BUILD_BROKEN",))
        self.assertEqual(red.standing,"BUILD_BROKEN")
        self.assertIsNone(red.receipt)
if __name__=="__main__": unittest.main()
