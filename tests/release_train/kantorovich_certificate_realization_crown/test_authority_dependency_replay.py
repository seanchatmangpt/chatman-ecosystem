import unittest
from scripts.release_train.kantorovich_certificate_realization_crown.authority import Action,admit
from scripts.release_train.kantorovich_certificate_realization_crown.dependencies import blockers
from scripts.release_train.kantorovich_certificate_realization_crown.receipt import Receipt,replay
from scripts.release_train.kantorovich_certificate_realization_crown import Refused
class T(unittest.TestCase):
    def test_fences(self):
        with self.assertRaises(Refused): admit(Action.DO)
        self.assertTrue(admit(Action.DO,'BRCE'))
        self.assertEqual(blockers({'root':['x']},{'x':'BUILD_BROKEN'}),{'x'})
        r=Receipt.make({'subject':'s'}); self.assertEqual(replay(r),'REPLAY_MATCH')
        bad=Receipt({**r.body,'actuation_performed':True},r.digest)
        with self.assertRaises(Refused): replay(bad)
        with self.assertRaises(Refused): blockers({'root':['x'],'x':['root']},{})
if __name__=='__main__': unittest.main()
