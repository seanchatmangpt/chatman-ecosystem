import unittest
from datetime import datetime, timezone, timedelta
from scripts.release_train.current_frontier.evidence import Evidence
from scripts.release_train.current_frontier.subject import Subject
from scripts.release_train.current_frontier.supersession import Supersession, validate_relations, Refusal
class T(unittest.TestCase):
 def rows(self):
  s=Subject.parse("o/r@"+"a"*40); t=datetime(2026,1,1,tzinfo=timezone.utc); return (Evidence("old",s,"REPOSITORY","PASS",t,"1"),Evidence("new",s,"REPOSITORY","FAIL",t+timedelta(minutes=1),"2"))
 def test_forward(self): self.assertEqual(len(validate_relations(self.rows(),(Supersession("old","new","NEW_RUN"),))),1)
 def test_backward_refuses(self):
  with self.assertRaises(Refusal): validate_relations(self.rows(),(Supersession("new","old","NEW_RUN"),))
