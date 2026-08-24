import unittest
from scripts.release_train.federation_convergence_crown.api import Subject,Epoch,qualify,replay,admit_action,Refused
from scripts.release_train.federation_convergence_crown.methodology import REQUIRED as METHODS
from scripts.release_train.federation_convergence_crown.rails import REQUIRED as RAILS
from scripts.release_train.federation_convergence_crown.failures import REQUIRED as FAILURES

class ChicagoCourt(unittest.TestCase):
    def world(self):
        s=Subject("seanchatmangpt/chatman-ecosystem","b"*40,"same",9)
        epochs=[Epoch(7,"stable",0,0),Epoch(8,"stable",0,0),Epoch(9,"stable",0,0)]
        rails={r:"digest" for r in RAILS}
        regions=[{"host":"h1","region":"r1","encrypted":True,"certificate":"c1","generation":9},{"host":"h2","region":"r2","encrypted":True,"certificate":"c2","generation":9}]
        return s,epochs,rails,regions
    def test_global_bounded_path_replays_without_do(self):
        s,epochs,rails,regions=self.world()
        q=qualify(subject=s,epochs=epochs,methods=METHODS,rails=rails,regions=regions,failures=FAILURES,correspondence=("same","same","same"))
        self.assertEqual(q["standing"],"PARTIAL_ALIVE")
        self.assertEqual(replay(q["receipt"],q["receipt"].digest()),"REPLAY_MATCH")
        with self.assertRaises(Refused): admit_action("DO")
    def test_broken_dependency_suppresses_receipt(self):
        s,epochs,rails,regions=self.world()
        q=qualify(subject=s,epochs=epochs,methods=METHODS,rails=rails,regions=regions,failures=FAILURES,correspondence=("same","same","same"),graph={"release":["external"]},failed_dependencies={"external"})
        self.assertEqual(q["standing"],"BLOCKED")
        self.assertIsNone(q["receipt"])

if __name__=="__main__": unittest.main()
