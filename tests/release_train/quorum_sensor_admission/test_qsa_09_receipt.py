import unittest
from dataclasses import replace
from scripts.release_train.quorum_sensor_admission import Receipt, Refused
class ReceiptCourt(unittest.TestCase):
 def test_seal_replays_and_tamper_refuses(self):
  r=Receipt("repo/x@"+"a"*40,1,"b"*64,"1/1","HEALTHY","STRICT_CURRENT",(),"PARTIAL_ALIVE","ok").seal(); r.replay()
  with self.assertRaises(Refused): replace(r,standing="ALIVE").replay()
 def test_reported_actuation_refuses(self):
  r=Receipt("repo/x@"+"a"*40,1,"b"*64,"1/1","HEALTHY","STRICT_CURRENT",(),"PARTIAL_ALIVE","ok").seal()
  with self.assertRaises(Refused): replace(r,actuation_performed=True).replay()
if __name__=="__main__": unittest.main()
