import sys,unittest
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.release_train.fusion_acquisition_admission.authority import ActionClass,admit_action
from scripts.release_train.fusion_acquisition_admission.receipt import Receipt
from scripts.release_train.fusion_acquisition_admission.errors import Refused
class TestAuthorityReceipt(unittest.TestCase):
    def test_do_and_tamper_refuse(self):
        with self.assertRaises(Refused): admit_action(ActionClass.DO)
        r=Receipt("o/r@"+"a"*40,1,"HEALTHY","PARTIAL_ALIVE",(),None,None).seal(); self.assertTrue(r.replay())
        with self.assertRaises(Refused): replace(r,actuation_performed=True).replay()
