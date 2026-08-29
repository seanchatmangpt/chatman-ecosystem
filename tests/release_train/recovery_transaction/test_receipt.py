import unittest
from scripts.release_train.recovery_transaction import Receipt
class T(unittest.TestCase):
 def test_replay_and_tamper(self):
  r=Receipt.make({'x':1});self.assertTrue(r.replay()); r.body['x']=2;self.assertFalse(r.replay())
 def test_authority_tamper(self):
  r=Receipt.make({'x':1});r.body['actuation_performed']=True;self.assertFalse(r.replay())
if __name__=='__main__':unittest.main()
