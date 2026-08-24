import unittest
from scripts.release_train.certificate_federation_realization_crown import *
from scripts.release_train.certificate_federation_realization_crown.refusal import Refused
class TestCalibrationDependencies(unittest.TestCase):
    def test_directional_calibration_and_current(self):
        s=Subject("o/r","2"*40,"x")
        def o(t,p,r): return Observation(s,3,t,t,"m"+t,"d"+t,TransportState.RESOLVED,Relation.EXACT,p,r,"2"*40,"a"*64,"b"*64)
        e=evaluate((o("a",True,False),o("b",False,True),o("c",True,True)))
        c=calibrate(3,e)
        self.assertEqual(c,current([c]))
        self.assertGreater(c.loss,0)
    def test_dependency_cycle_refuses(self):
        with self.assertRaises(Refused): blockers({"root":("a",),"a":("root",)}, {}, "root")
