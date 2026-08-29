import unittest
from datetime import datetime, timezone, timedelta
from scripts.release_train.current_frontier.evidence import Evidence
from scripts.release_train.current_frontier.subject import Subject
from scripts.release_train.current_frontier.supersession import Supersession
from scripts.release_train.current_frontier.frontier import resolve_frontier, standing
class T(unittest.TestCase):
 def test_stale_green_new_red(self):
  s=Subject.parse("o/r@"+"a"*40); t=datetime(2026,1,1,tzinfo=timezone.utc); old=Evidence("old",s,"REPOSITORY","PASS",t,"1"); new=Evidence("new",s,"REPOSITORY","FAIL",t+timedelta(seconds=1),"2"); f=resolve_frontier((old,new),(Supersession("old","new","NEW_RUN"),)); self.assertEqual([e.evidence_id for e in f.current],["new"]); self.assertEqual(standing(f),"BUILD_BROKEN")
