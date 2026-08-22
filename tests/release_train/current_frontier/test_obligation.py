import unittest
from datetime import datetime, timezone
from scripts.release_train.current_frontier.evidence import Evidence
from scripts.release_train.current_frontier.subject import Subject
from scripts.release_train.current_frontier.frontier import Frontier
from scripts.release_train.current_frontier.obligation import Obligation, coverage, require_complete, Refusal
class T(unittest.TestCase):
 def test_focused_cannot_cover_repo(self):
  e=Evidence("x",Subject.parse("o/r@"+"a"*40),"FOCUSED","PASS",datetime.now(timezone.utc),"1"); f=Frontier((e,),()); o=(Obligation("repo","REPOSITORY"),); self.assertEqual(coverage(f,o)["repo"],"MISSING")
  with self.assertRaises(Refusal): require_complete(coverage(f,o),o)
