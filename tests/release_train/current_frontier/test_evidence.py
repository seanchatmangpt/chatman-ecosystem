import unittest
from datetime import datetime, timezone
from scripts.release_train.current_frontier.evidence import Evidence, Refusal
from scripts.release_train.current_frontier.epoch import Epoch
from scripts.release_train.current_frontier.subject import Subject
class T(unittest.TestCase):
 def setUp(self): self.e=Epoch(datetime(2026,1,1,tzinfo=timezone.utc),datetime(2026,1,2,tzinfo=timezone.utc)); self.s=Subject.parse("o/r@"+"a"*40)
 def test_run_bound(self): self.assertIsNotNone(Evidence("e",self.s,"REPOSITORY","PASS",self.e.start,"1").admit(self.e))
 def test_missing_run_refuses(self):
  with self.assertRaises(Refusal): Evidence("e",self.s,"REPOSITORY","PASS",self.e.start).admit(self.e)
