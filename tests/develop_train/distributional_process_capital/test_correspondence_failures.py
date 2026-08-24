import unittest
from scripts.develop_train.distributional_process_capital.errors import Refused
from scripts.develop_train.distributional_process_capital.methodology import REQUIRED,require_methods
from scripts.develop_train.distributional_process_capital.correspondence import EngineWitness,RegionWitness,require_engines,require_regions
from scripts.develop_train.distributional_process_capital.failures import World,require_complete
class CorrespondenceCourt(unittest.TestCase):
    def test_full_correspondence(self):
        require_methods(REQUIRED)
        require_engines([EngineWitness("BEAM","i1","m1","s","t","o"),EngineWitness("WASM","i2","m2","s","t","o")])
        require_regions([RegionWitness("h1","r1",True,"c1",4),RegionWitness("h2","r2",True,"c2",4)])
        self.assertEqual(len(require_complete(list(World))),7)
    def test_tls_laundering_refuses(self):
        with self.assertRaises(Refused): require_regions([RegionWitness("h1","r1",False,"",4),RegionWitness("h2","r2",True,"c2",4)])
if __name__=="__main__": unittest.main()
