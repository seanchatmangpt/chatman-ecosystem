import unittest
from scripts.develop_train.process_evidence_correspondence import *

class TestChicago(unittest.TestCase):
    def test_full_bounded_path_and_red_dominance(self):
        subject=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"8"*40+"#"+"9"*64)
        engines=[EngineWitness("BEAM","beam","sem","trace","obl"),EngineWitness("WASM","wasm","sem","trace","obl")]
        regions=[RegionWitness("host-a","us",7,100,200,True,"c"*64,"sem"),RegionWitness("host-b","eu",7,101,201,True,"c"*64,"sem")]
        oracles=[OracleWitness("POWL","p1","m1","sem","pv"),OracleWitness("POWL","p2","m2","sem","pv"),OracleWitness("OCEL","o1","n1","sem","ov"),OracleWitness("OCEL","o2","n2","sem","ov")]
        root=replay_root([ReplayNode("semantic","1"*64),ReplayNode("reactor","2"*64,("semantic",)),ReplayNode("projection","3"*64,("reactor",))])
        qualified=qualify(subject,7,"CONSERVATIVE",REQUIRED,engines,regions,oracles,REQUIRED_FAILURES,["PARTIAL_ALIVE"],root,150)
        self.assertEqual(qualified.standing,"PARTIAL_ALIVE")
        self.assertIsNotNone(qualified.receipt)
        self.assertEqual(replay(qualified.receipt,qualified.receipt.digest()),"REPLAY_MATCH")
        red=qualify(subject,7,"CONSERVATIVE",REQUIRED,engines,regions,oracles,REQUIRED_FAILURES,["PARTIAL_ALIVE","BUILD_BROKEN"],root,150)
        self.assertEqual(red.standing,"BUILD_BROKEN")
        self.assertIsNone(red.receipt)

if __name__ == "__main__": unittest.main()
